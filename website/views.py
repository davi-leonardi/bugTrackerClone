import re
from flask import flash, redirect, render_template, Blueprint, request, url_for
from flask_login import current_user, login_required, logout_user
from flask_socketio import join_room, leave_room
from werkzeug.security import check_password_hash, generate_password_hash
import json

from .models import Project, Ticket, Usr, Chat, association_table, ticketDevTeam
from . import io, db

views = Blueprint('views', __name__)

@views.route('/', methods=['POST', 'GET'])
@login_required
def home():

    if request.method == 'POST':
        name = request.form.get("name")
        description = request.form.get("description")
        owner = current_user.id
        contributors = request.form.getlist("team")

        prj = Project.query.filter_by(name=name).first()

        if prj:
            flash("A project with the same name already exists!", category="error")
        else:
            if(len(name) > 30 or len(name) < 2):
                flash("Invalid name", category="error")
            elif(len(description) > 100):
                flash("Description is too long!", category="error")
            else:
                new_prj = Project(name=name, description=description, owner=owner, status="Open")
                db.session.add(new_prj)

                for c in contributors:
                    team_member = Usr.query.get(int(c))
                    current_user.projects.append(new_prj)
                    team_member.projects.append(new_prj)

                db.session.commit()
                flash("Project created!", category="success")

    return render_template("home.html", usernames=Usr.query.all(), projects=Project.query.all(), user=current_user)

@views.route('/employees')
@login_required
def employees():

    employees = Usr.query.all()
    numOfEmployees = Usr.query.count()

    return render_template("employees.html", employees=employees, numOfEmployees=numOfEmployees)

@views.route('/employees/updateEmp', methods=['POST'])
@login_required
def updateEmp():

    if request.method == 'POST':
        id = request.form.get("eid")
        name = request.form.get("ename")
        email = request.form.get("eemail")
        password = request.form.get("epassword")
        checkbox = request.form.get("changePassword")

        if(check_password_hash(current_user.password, password)):
            user = Usr.query.get(id)
            
            if not re.match("^[A-Za-z]+[ ][A-Za-z]+$", str(name)):
                flash("Invalid name", category="error") 
            elif (len(name) > 30):
                flash("Invalid name length, it should be under <30 chars", category="error")
            elif not re.match("^[0-9a-z._]+[@][a-z]+\.[A-Za-z]+$", str(email)):
                flash("Invalid email", category="error")
            elif(len(email) > 30):
                flash("Invalid email length, it should be <30 chars", category="error")
            elif (len(password) < 6 or len(password) > 20):
                flash("Invalid password length, it should be between 6 - 20 chars", category="error")
            else:
                user.full_name = name
                user.email = email

                if(checkbox == 'true'):
                    newPassword = request.form.get("enpassword")
                    user.password = generate_password_hash(newPassword, method='sha256')
                
                db.session.commit()
                flash("User updated!", category="success")

    return redirect(url_for("views.employees"))

@views.route('/employees/deleteUser')
@login_required
def deleteUser():

    id = current_user.id
    user = Usr.query.get(id)
    prjs = Project.query.all()

    if user:

        for p in prjs:
            if(p.owner == id):
                for mes in p.messages:
                    db.session.delete(mes)

                for tic in p.tickets:
                    db.session.delete(tic)

                db.session.delete(p) 

        db.session.commit()

        db.session.execute('DELETE FROM "ticketDevTeam" WHERE usr_id = :val', {'val': id})
        db.session.commit()
        
        db.session.execute('DELETE FROM association_table WHERE usr_id = :val', {'val': id})
        db.session.commit()
            
        db.session.delete(user)
        db.session.commit()
        logout_user()

        flash("User account deleted", category="success")
    
    return redirect(url_for('auth.login'))

@views.route('/project/<int:id>')
@login_required
def project(id):
 
    this_project = Project.query.get(id)
    users = Usr.query.all()
    freeUsers = []
    assignedUsers = []
    numOfTickets = 0

    for c in this_project.usrs:
        assignedUsers.append(c.id);
    
    for u in users:
        if(u.id not in assignedUsers):
            freeUsers.append(u)
    
    for n in this_project.tickets:
        numOfTickets += 1
    
    return render_template("project.html", this_project=this_project, usernames=users, freeUsers=freeUsers, numOfTickets=numOfTickets)

@views.route('/project/<int:id>/updateProj', methods=['GET', 'POST'])
@login_required
def update_proj(id):
    if request.method == 'POST':
        name = request.form.get('pname')
        description = request.form.get('pdescription')
        status = request.form.get('pstatus')

        if(len(name) > 30 or len(name) < 2):
            flash("Invalid name", category="error")
        elif(len(description) > 100):
            flash("Description is too long!", category="error")
        else:
            proj = Project.query.filter_by(id=id).first()
            print(proj.name)
            print(name)
            proj.name = name
            proj.description = description
            proj.status = status
            db.session.commit()

            flash("Project updated!", category="success")
    
    return redirect(url_for("views.project", id=id))

@views.route('/project/<int:id>/deleteProj')
@login_required
def deleteProj(id):
    prj = Project.query.get(id)

    if prj:

        db.session.execute('DELETE FROM association_table WHERE project_id = :val', {'val': id})
        
        for m in prj.messages:
            db.session.delete(m)

        for t in prj.tickets:
            db.session.delete(t)

        db.session.delete(prj)
        db.session.commit()
        flash("Project deleted", category="success")

    return redirect("/") 

@views.route('/project/<int:id>/addTeamMem', methods=['POST', 'GET'])
@login_required
def addTeamMem(id):
    if request.method == 'POST':
        usersToBeAdded = request.form.getlist("team")

        for c in usersToBeAdded:
            team_member = Usr.query.get(int(c))
            this_project = Project.query.get(int(id))
            team_member.projects.append(this_project)
        
        db.session.commit()
        flash("Member added!", category="success")

    return redirect(url_for("views.project", id=id))

@views.route('/project/<int:id>/deleteTeamMem', methods=['POST', 'GET'])
@login_required
def deleteTeamMem(id):
    if request.method == 'POST':
        userToDelete = request.form.get("memId")
        db.session.execute('DELETE FROM association_table WHERE usr_id = :val', {'val': userToDelete})
        db.session.commit()
        flash("Member deleted!", category="success")

    return redirect(url_for("views.project", id=id))

@views.route('/project/<int:id>/addTicket', methods=['POST', 'GET'])
@login_required
def addTicket(id):
    if request.method == 'POST':
        tckid = request.form.get('tckToBeUpdated')
        name = request.form.get('ticketname')
        description = request.form.get('description')
        status = request.form.get('status')
        priority = request.form.get('priority')
        type = request.form.get('type')
        devsTeam = request.form.getlist('devsTeam')
        owner = current_user.id

        if(len(name) > 40 or len(name) < 2):
                flash("Invalid name", category="error")
        elif(len(description) > 500):
                flash("Description is too long!", category="error")
        else:
            if tckid != "":
                tck = Ticket.query.filter_by(id=tckid).first()
                tck.name = name
                tck.description = description
                tck.status = status
                tck.priority = priority
                tck.type = type
                tck.project_id = id
                tck.owner = owner

                db.session.execute('DELETE FROM "ticketDevTeam" WHERE ticket_id = :val', {'val': tckid})
                db.session.commit()
                flash("Ticket has been updated!", category="success")
            else:
                tck = Ticket(name=name, description=description, status=status, priority=priority, type=type, project_id=id, owner=owner)
                db.session.add(tck)
                db.session.commit()
                flash("Ticket has been created!", category="success")

            for c in devsTeam:
                team_member = Usr.query.get(int(c))
                team_member.ticketTeam.append(tck)
                db.session.commit()

    return redirect(url_for("views.project", id=id))

@views.route('/project/<int:id>/deleteTicket', methods=['POST', 'GET'])
@login_required
def deleteTicket(id):
    if request.method == 'POST':
        tckToDelete = request.form.get("tckId")
        tck = Ticket.query.filter_by(id=tckToDelete).first()
        if tck:
            db.session.execute('DELETE FROM "ticketDevTeam" WHERE ticket_id = :val', {'val': tckToDelete})

            for t in tck.messages:
                db.session.delete(t)

            db.session.delete(tck)
            db.session.commit()
            flash("Ticket deleted!", category="success")

    return redirect(url_for("views.project", id=id))

@views.route('/project/<int:id>/updateProjMan', methods=['POST'])
@login_required
def updateProjMan(id):
    if request.method == 'POST':
        newProjMan = request.form.get("team")
        prj = Project.query.filter_by(id=id).first()

        if prj:
            prj.owner = newProjMan
            db.session.commit()
            flash("Project Manager Changed!", category="success")
    
    return redirect(url_for("views.project", id=id))

@views.route('/tickets', methods=['GET', 'POST'])
@login_required
def display_tickets():

    usernames = Usr.query.all()
    tickets = Ticket.query.all()
    numOfTickets = Ticket.query.count()
    allProjects = Project.query.all()

    return render_template("tickets.html", tickets=tickets, usernames=usernames, projects=allProjects, numOfTickets=numOfTickets)

@io.on('userConnected')
def handle_message(data):
    print('received message: ' + str(data))
    io.send('Message received: ' + str(data))

@io.on('displayTicketInfo')
def handle_ticket_info(id):
    tck = Ticket.query.get(id)
    tckOwner = Usr.query.get(tck.owner)
    jsonDevs = []

    for t in tck.devs:
        jsonDevs.append(str(t.full_name))

    data = {
    'tckid' : id,    
    'tckName' : tck.name,
    'tckDesc' : tck.description,
    'tckStatus' : tck.status,
    'tckPriority' : tck.priority,
    'tckType' : tck.type,
    'tckAuthor' : tckOwner.full_name,
    'tckDevs' : jsonDevs
    }

    jsonData = json.dumps(data)
    io.emit('handleTicketInfo', jsonData, json=True)

def serializeChat(chat):
    serializedData = {}
    data = []

    for i in chat:
        serializedData = {
            'id': i.id,
            'name': i.ownerName,
            'date': i.post_date.strftime("%d/%m/%y at %H:%M"),
            'content': i.content
        }

        data.append(serializedData)

    return data

@io.on('joinChat')
def join_chat(id, old_room):
    if(old_room != 0):
        leave_room(old_room)
    join_room(id)
    tck = Ticket.query.get(id)
    io.emit('loadChat', serializeChat(tck.messages), to=id)

@io.on('sendComment')
def handle_comment(data):
    commentOwner = Usr.query.get(data['owner'])
    tck = Ticket.query.get(data['ticketID'])

    if(len(data['content']) < 100 and commentOwner and tck):
        new_chat = Chat(ownerName=commentOwner.full_name, content=data['content'], ticket_id=tck.id, project_id=tck.project_id, owner=commentOwner.id)
        db.session.add(new_chat)
        db.session.commit()
        new_tck = Ticket.query.get(data['ticketID'])
    else:
        flash("Comment is too long!", category="error")

    io.emit('loadChat', serializeChat(new_tck.messages), to=data['ticketID'])

@io.on('deleteComment')
def deleteComment(tck_id, msg_id):

    msgToDel = Chat.query.filter_by(id=msg_id).first()

    if msgToDel:
        db.session.delete(msgToDel)
        db.session.commit()

    tck = Ticket.query.get(tck_id)

    io.emit('loadChat', serializeChat(tck.messages), to=tck_id)
