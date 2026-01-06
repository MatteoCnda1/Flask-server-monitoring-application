from app.models.host import Host, User
from app.models.evenements import Journal
from flask import Blueprint, render_template, redirect, url_for, request, session, flash
import os
import datetime
from app.models.evenements import Journal

host_bp = Blueprint('user', __name__, template_folder='./../templates')

@host_bp.route('/')
@host_bp.route('/', methods=['GET','POST'])
def index():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        
        user = User.authentificate(username, password)

        if user:
            session['loggedin'] = True
            session['id'] = user.id
            session['username'] = user.nom_user
            session['role_id'] = user.role_id
            flash('Logged in successfully', 'success')
            return render_template('index.html')
        else:
            msg = "Incorrect username/password !"
    return render_template('index.html')


@host_bp.route('/server_management', methods=['POST','GET'])
def server_management():
    
    if 'loggedin' not in session:
        return redirect(url_for('user.index'))
   
    user_role = session.get('role_id')
    if user_role not in [1,2]:
        flash('Access denied : Insuffisant Privileges', 'error')
        return redirect(url_for('user.index'))

    hosts = Host.query.all()
    return render_template('server_management.html', hosts=hosts)


@host_bp.route('/user_management')
def user_management():

    if 'loggedin' not in session:
        return redirect(url_for('user.index'))
    
    user_role = session.get('role_id')
    if user_role != 1:
        flash('Access denied Administrator Only ! ', 'error')
        return redirect(url_for('user.index'))

    users = User.query.all()
    return render_template('user_management.html', users=users)

@host_bp.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    flash('Successfully logout', 'success')
    return redirect(url_for('user.index'))

@host_bp.route('/add_server', methods=['POST','GET'])
def add_server():

    if 'loggedin' not in session:
        flash('You must be connected', 'error')
        return redirect(url_for('user.index'))

    user_role = session.get('role_id')
    if user_role !=1:
        flash('Access only for administrators', 'error')
        return redirect(url_for('user.index'))

    if request.method == 'POST':

            hostname = request.form.get("nom")
            ipv4 = request.form.get("ipv4")

            if not hostname or not ipv4:
                flash('You must complete all the fields !', 'error')
                return redirect(url_for('user.server_management'))

            result = Host.ajoute_host(hostname, ipv4)
            if result == "success":
                flash('Server added successfully', 'success')
            else:
                flash(result,'error')
            return redirect(url_for('user.server_management'))
    return render_template('server_management.html')

@host_bp.route('/delete/<id>')
def delete_server(id):

    if 'loggedin' not in session:
        flash('You must be connected !', 'error')
        return redirect(url_for('user.index'))
    
    user_role = session.get('role_id')
    if user_role not in [1, 2]:
        flash('Access only for administrators', 'error')
        return redirect(url_for('user.index'))

    host = Host.query.get(id)
    if host:
        Host.supprime_host(id)

    return redirect(url_for('user.server_management'))

@host_bp.route('/add_user', methods=['GET','POST'])
def add_user():

    if 'loggedin' not in session:
        flash('You must be connected', 'error')
        return redirect(url_for('user.index'))
    
    user_role = session.get('role_id')
    if user_role != 1:
        flash('Access only for administrators', 'error')
        return redirect(url_for('user.index'))

    if request.method == 'POST':
        username = request.form.get('nom')
        pwd = request.form.get('password')
        role = request.form.get('role')

        if not username or not role:
            flash('You must complete all the fields !', 'error')
            return redirect(url_for('user.user_management'))
        
        try:
            role = int(role)
        except (ValueError, TypeError):
            flash('Invalid role!', 'error')
            return redirect(url_for('user.usermanagement'))

        result = User.create_user(username, pwd, role)
        if result == "success":
            flash('User added successfully', 'success')
        else:
            flash(result, 'error')
        return redirect(url_for('user.user_management'))

@host_bp.route('/delete_user/<id>')
def delete_user(id):

    if 'loggedin' not in session:
        flash('You must be connected !', 'error')
        return redirect(url_for('user.index'))
    
    user_role = session.get('role_id')
    if user_role not in [1, 2]:
        flash('Access reversed for administrators or supervisors', 'error')
        return redirect(url_for('user.index'))

    user = User.query.get(id)
    if user:
        User.del_user(id)

    return redirect(url_for('user.user_management'))

@host_bp.route('/edit_user/<int:user_id>', methods=['GET'])
def edit_user(user_id):

    if 'loggedin' not in session:
        flash('Vous devez être connecté', 'error')
        return redirect(url_for('user.index'))
    

    if session.get('role_id') != 1:
        flash('Accès réservé aux administrateurs', 'error')
        return redirect(url_for('user.log_choice'))
    

    user = User.query.get(user_id)
    
    if not user:
        flash('Utilisateur non trouvé', 'error')
        return redirect(url_for('user.user_management'))
    
    return render_template('edit_user.html', user=user)

@host_bp.route('/update_user/<user_id>', methods=['POST'])
def update_user(user_id):

    if 'loggedin' not in session:
        flash('You must be logged', 'error')
        return redirect(url_for('user.index'))
    
    if session.get('role_id') != 1:
        flash('Only admin access', 'error')
        return redirect(url_for('user.log_choice'))
    
    username = request.form.get('username', '').strip()
    password1 = request.form.get('password1', '').strip()
    password2 = request.form.get('password2', '').strip()
    role = request.form.get('role')
    
    if not username:
        flash('Username is empty.', 'error')
        return redirect(url_for('user.edit_user', user_id=user_id))
    
    if password1 or password2:
        if password1 != password2:
            flash('Password are differents', 'error')
            return redirect(url_for('user.edit_user', user_id=user_id))
        password = password1
    else:
        password = None  
    
    try:
        role = int(role) if role else None
    except ValueError:
        flash('Invalid role', 'error')
        return redirect(url_for('user.edit_user', user_id=user_id))
    
    result = User.modify_user(user_id, username=username, password=password, role=role)
    
    if result == "success":
        flash('User modified !', 'success')
        return redirect(url_for('user.user_management'))
    else:
        flash(result, 'error')
        return redirect(url_for('user.edit_user', user_id=user_id))
    

@host_bp.route('/edit_server/<int:host_id>', methods=['GET'])
def edit_server(host_id):

    if 'loggedin' not in session:
        flash('You must be logged', 'error')
        return redirect(url_for('user.index'))
    
    if session.get('role_id') not in [1, 2]:
        flash('Only admin or supervisor access', 'error')
        return redirect(url_for('user.log_choice'))
    
    host = Host.query.get(host_id)
    
    if not host:
        flash('Server not found', 'error')
        return redirect(url_for('user.server_management'))
    
    return render_template('edit_server.html', host=host)

@host_bp.route('/update_server/<int:host_id>', methods=['POST'])
def update_server(host_id):

    if 'loggedin' not in session:
        flash('You must be logged', 'error')
        return redirect(url_for('user.index'))
    
    if session.get('role_id') not in [1, 2]:
        flash('Only admin or supervisor access', 'error')
        return redirect(url_for('user.log_choice'))
    
    hostname = request.form.get('hostname', '').strip()
    ipv4 = request.form.get('ipv4', '').strip()
    
    if not hostname:
        flash('Hostname cannot be empty', 'error')
        return redirect(url_for('user.edit_server', host_id=host_id))
    
    if not ipv4:
        ipv4 = None
    
    result = Host.modify_server(host_id, hostname=hostname, ipv4=ipv4)
    
    if result == "success":
        flash('Server modified successfully!', 'success')
        return redirect(url_for('user.server_management'))
    else:
        flash(result, 'error')
        return redirect(url_for('user.edit_server', host_id=host_id))

@host_bp.route('/log_choice', methods=['GET'])
def log_choice():
    if 'loggedin' not in session:
        flash('You must be logged in', 'error')
        return redirect(url_for('user.index'))
    
    machines = Host.query.all()
    return render_template('log_choice.html', machines=machines)

@host_bp.route('/view_logs', methods=['POST'])
def view_logs():
    if 'loggedin' not in session:
        flash('You must be logged in', 'error')
        return redirect(url_for('user.index'))
    
    machine_ids = request.form.getlist('machine_ids')
    
    sort_order = request.form.get('sort_order', 'desc')
    nb_lignes = int(request.form.get('nb_lignes', 100))

    if not machine_ids:
        flash('Please select at least one server !', 'error')
        return redirect(url_for('user.log_choice'))
    key_file = os.path.expanduser('~/.ssh/id_rsa_superv')
    
    
    all_evenements = []
    machines_info = []
    errors = []
    
    print(f"[DEBUG] Retrieve logs from {len(machine_ids)} server(s)")
    
    # retrieve logs from selected machines
    for machine_id in machine_ids:
        try:
            machine = Host.query.get(int(machine_id))
            
            if not machine:
                errors.append(f"Server ID {machine_id} not found")
                continue
            
            machines_info.append(machine)
            
            print(f"[DEBUG] Retrieve logs from {machine.hostname} ({machine.ipv4})")
            
            
            journal = Journal.recuperer_logs_distant(
                ip=machine.ipv4,
                user='superv',
                key_file=key_file,
                log_path='/var/log/syslog',
                nb_lignes=nb_lignes
            )
            
            if journal and journal.liste():
                
                for evt in journal.liste():
                    # add a property to id the source
                    evt._source_hostname = machine.hostname
                    evt._source_ip = machine.ipv4
                    all_evenements.append(evt)
                
                print(f"[DEBUG] {len(journal.liste())} events retrieved by {machine.hostname}")
            else:
                errors.append(f"No logs retrieved from {machine.hostname}")
                
        except Exception as e:
            error_msg = f"Error retrieving logs from {machine.hostname if 'machine' in locals() else 'server'}: {str(e)}"
            errors.append(error_msg)
            print(f"[ERREUR] {error_msg}")
    
    
    if errors:
        for error in errors:
            flash(error, 'warning')
    

    if not all_evenements:
        flash('No logs found from selected servers', 'error')
        return redirect(url_for('user.log_choice'))
    
    
    if sort_order == 'desc':
        all_evenements.sort(key=lambda evt: evt.info()['date_heure'], reverse=True)
    else:
        all_evenements.sort(key=lambda evt: evt.info()['date_heure'])
    
    retrieved_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"[DEBUG] Total : {len(all_evenements)} events of {len(machines_info)} server(s)")
    
    return render_template('view_logs.html', 
                           evenements=all_evenements, 
                           machines=machines_info,
                           retrieved_at=retrieved_at,
                           total_events=len(all_evenements))
