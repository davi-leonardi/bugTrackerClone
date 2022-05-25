from flask import flash, redirect, render_template, Blueprint, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import true

from .models import Project, Ticket, Usr, association_table
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
                new_prj = Project(name=name, description=description, owner=owner, status=True)
                db.session.add(new_prj)

                for c in contributors:
                    team_member = Usr.query.get(int(c))
                    current_user.projects.append(new_prj)
                    team_member.projects.append(new_prj)

                db.session.commit()
                flash("Project created!", category="success")

    return render_template("home.html", usernames=Usr.query.all(), projects=Project.query.all(), user=current_user)

@views.route('/projects')
@login_required
def projects():
    pass

@views.route('/project/<int:id>')
@login_required
def project(id):
 
    this_project = Project.query.get(id)
    users = Usr.query.all()
    freeUsers = []
    assignedUsers = []

    for c in this_project.usrs:
        assignedUsers.append(c.id);
    
    for u in users:
        if(u.id not in assignedUsers):
            freeUsers.append(u)
    
    return render_template("project.html", this_project=this_project, usernames=users, freeUsers=freeUsers)

@views.route('/project/<int:id>/addTeamMem', methods=['POST', 'GET'])
@login_required
def addTeamMem(id):
    if request.method == 'POST':
        usersToBeAdded = request.form.getlist("team")
        print(usersToBeAdded)

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
        name = request.form.get('name')
        description = request.form.get('description')
        status = request.form.get('status')
        priority = request.form.get('priority')
        type = request.form.get('type')
        owner = current_user.id

        tck = Ticket.query.filter_by(name=name).first()

        if tck:
            flash("A ticket with the same name already exists!", category="error")
        else:
            if(len(name) > 40 or len(name) < 2):
                flash("Invalid name", category="error")
            elif(len(description) > 1000):
                flash("Description is too long!", category="error")
            else:
                new_tck = Ticket(name=name, description=description, status=status, priority=priority, type=type, project_id=id, owner=owner)
                db.session.add(new_tck)
                db.session.commit()
                flash("Ticket has been created!", category="success")

    return redirect(url_for("views.project", id=id))

@views.route('/project/<int:id>/deleteTicket', methods=['POST', 'GET'])
@login_required
def deleteTicket(id):
    if request.method == 'POST':
        tckToDelete = request.form.get("tckId")
        tck = Ticket.query.filter_by(id=tckToDelete).first()
        if tck:
            db.session.delete(tck)
            db.session.commit()
            flash("Member deleted!", category="error")

    return redirect(url_for("views.project", id=id))

@io.on('userConnected')
def userConnected(msg):
    io.send(msg)
    
