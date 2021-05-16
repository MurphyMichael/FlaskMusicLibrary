from flask import render_template, url_for, flash, redirect, request
from musiclib import app, conn, bcrypt, mysql
from musiclib.forms import RegisterForm, LoginForm, SearchForm, PlaylistForm
from musiclib.models import MyUser
from flask_login import login_user, current_user, logout_user, login_required
from datetime import date

# homepage is the login page
@app.route('/', methods=['GET', 'POST'])
def Login():
    # redirect the user to the account page if they're already logged in
    if current_user.is_authenticated:
       return redirect(url_for('Account'))
    # grab the information from the login form
    form = LoginForm()
    # check information when a valid form is submitted
    if form.validate_on_submit():
        # create a connection to the database and select the user based on the given email
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM User WHERE email = %s", (form.email.data))
        temp = cur.fetchone()
        cur.close()
        # if there is a User with the given email
        if temp != None:
            user = MyUser(temp[0], temp[1], temp[2], temp[3])
            # check password hash and login if it matches
            if bcrypt.check_password_hash(user.password, form.password.data):
                flash('You\'ve logged in successfully!', 'success')
                login_user(user, remember=form.remember.data)
                return redirect(url_for('Search'))
            # password doesn't match
            else:
                flash('Login Unsuccessful. Check email and password', 'danger')
        # email doesn't exist
        else:
            flash('Email doesn\'t exist. Please register before logging in.', 'danger')
    return render_template('login.html', title='Login', form=form)
    
# register page
@app.route('/register', methods=['GET', 'POST'])
def Register():
    # redirect the user to the account page if they're already logged in
    if current_user.is_authenticated:
       return redirect(url_for('Account'))
    # grab the information from the register form
    form = RegisterForm()
    # check information when a valid form is submitted
    if form.validate_on_submit():
        # create a connection to the database and insert the new user
        conn = mysql.connect()
        cur = conn.cursor()
        # hash the given password
        hashPass = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        cur.execute("INSERT INTO User(username, password, email) VALUES(%s, %s, %s)", (form.username.data, hashPass, form.email.data))
        conn.commit()
        cur.close()
        conn.close()
        flash("Your account has been created!", 'success')
        # redirect to login page once registered
        return redirect(url_for('Login'))
    return render_template('register.html', title='Search', form=form)

# account page
@app.route('/account', methods=['GET', 'POST'])
@login_required
def Account():
    # Display all of the current user's playlists from both public and private on their account page
    username = current_user.get_user()
    cur = conn.cursor()
    cur.execute("SELECT * FROM PublicPlaylist WHERE userid=%s", current_user.get_id())
    public=cur.fetchall()
    cur.execute("SELECT * FROM PrivatePlaylist WHERE userid=%s", current_user.get_id())
    private=cur.fetchall()
    cur.close()
    return render_template('account.html', title='Account', username=username, public=public, private=private)

# search page
@app.route('/search', methods=['GET', 'POST'])
@login_required
def Search():
    # get all information from the search form and forward them to the results page
    search = SearchForm(request.form)
    if request.method == 'POST':
        return Results(search)
    return render_template('search.html', title='Search', form=search)

# results page
@app.route('/results')
@login_required
def Results(search):
    results = []
    searchStr = search.data['search']
    # if there is a table selected
    if(search.select.data != None):
        table = search.select.data
        cur = conn.cursor()
        # if multiple things are selected, gather all data from the appropriate table
        if search.data['search'] == '': 
            if(table == 'Artist'):
                cur.execute("SELECT * FROM Artist")
                results = cur.fetchall()
            elif(table == 'Album'):
                cur.execute("SELECT * FROM Album")
                results = cur.fetchall()
            elif(table == 'Songs'):
                cur.execute("SELECT * FROM Song")
                results = cur.fetchall()
            elif(table == 'User'):
                # don't display current user
                cur.execute("SELECT * FROM User WHERE id <> %s", current_user.get_id())
                results = cur.fetchall()
            else:
                flash('Invalid table selection')
                cur.close()
                return redirect(url_for('Search'))
         # if one thing is selected, gather all data from the appropriate table based on the search given
        else:
            if(table == 'Artist'):
                cur.execute("SELECT * FROM Artist WHERE name = %s or genre = %s", (search.data['search'], search.data['search']))
                results = cur.fetchall()
            elif(table == 'Album'):
                cur.execute("SELECT * FROM Album WHERE title = %s or genre = %s", (search.data['search'], search.data['search']))
                results = cur.fetchall()
            elif(table == 'Songs'):
                cur.execute("SELECT * FROM Song WHERE title = %s or genre = %s", (search.data['search'], search.data['search']))
                results = cur.fetchall()
            elif(table == 'User'):
                cur.execute("SELECT * FROM User WHERE username = %s or email = %s", (search.data['search'], search.data['search']))
                results = cur.fetchall()
            else:
                flash('Invalid table selection')
                cur.close()
                return redirect(url_for('Search'))
        cur.close()
    # if there is no table selected
    else:
        flash('Table not selected', 'info')
        return redirect(url_for('Search'))
    # no results found
    if not results:
        flash('Results not found', 'info')
        return redirect(url_for('Search'))
    # results found
    else:
        return render_template('results.html', title='Results', results=results, table=table)

# artist page
@app.route('/artist')
@login_required
def Artist():
    # display all albums by the selected artist
    artistID= request.args.get('artistID')
    cur = conn.cursor()
    cur.execute("SELECT name, genre FROM Artist WHERE id = %s", (artistID))
    artist = cur.fetchone()
    cur.execute("SELECT * FROM Album WHERE artistID = %s", (artistID))
    results = cur.fetchall()
    cur.close()
    # forward all albums
    if results != None:
        return render_template('artist.html', title='Artist', results=results, artistname=artist[0], genre=artist[1])
    # display that no albums exist
    else:
        flash("Artist has no albums in our database.")
        return redirect(url_for('Search'))

# album page
@app.route('/album')
@login_required
def Album():
    # display all songs in the selected album
    albumID= request.args.get('albumID')
    cur = conn.cursor()
    cur.execute("SELECT artistID, title FROM Album WHERE id = %s", (albumID))
    artist = cur.fetchone()
    cur.execute("SELECT name FROM Artist WHERE id = %s", (artist[0]))
    artistname = cur.fetchone()
    cur.execute("SELECT * FROM Song WHERE albumID = %s", (albumID))
    results = cur.fetchall()
    cur.close()
    # forward all songs
    if results != None:
        return render_template('album.html', artistname=artistname[0], title=artist[1], results=results, genre=results[0][2])
    # display that no songs exist
    else:
        flash("Album has no songs in our database.", 'info')
        return redirect(url_for('Search'))
    return render_template('album.html', title='Album')

# song page
@app.route('/songs')
@login_required
def Song():
    # display all relevant information for the selected song
    songID= request.args.get('songID')
    cur = conn.cursor()
    cur.execute("SELECT Song.title, Song.genre, Song.length, Album.title, Artist.name FROM Song, Album, Artist WHERE Song.artistID = Artist.id AND Song.albumID = Album.id AND Song.id = %s", (songID))
    results = cur.fetchone()
    cur.close()
    # forward all song information
    if results != None:
        return render_template('songs.html', results=results, songID=songID)
    # display that the song doesn't exist
    else:
        flash("This song wasn't found in our database.", 'info')
        return redirect(url_for('Search'))
    return render_template('songs.html', title='Song')

# user page
@app.route('/user')
@login_required
def UserPage():
    # display all public playlists by the selected user
    userID= request.args.get('userID')
    results=()
    cur = conn.cursor()
    cur.execute("SELECT username FROM User where id = %s", userID)
    username=cur.fetchone()
    cur.execute("SELECT * FROM PublicPlaylist WHERE userid=%s", userID)
    results = cur.fetchall()
    cur.close()
    return render_template('publicaccount.html', title='User', username=username[0], results=results)

# view specific public playlist page
@app.route('/view')
@login_required
def ViewPlaylist():
    # display all songs in the selected playlist and allow deletion if from the account page
    candelete= request.args.get('candelete')
    playlistID=request.args.get('playlistID')
    name=request.args.get('name')
    cur = conn.cursor()
    cur.execute("SELECT PublicSongs.songid, Song.title, Artist.name, Album.title FROM PublicSongs, Song, Artist, Album WHERE PublicSongs.playlistID = %s AND PublicSongs.songid = Song.id AND Artist.id = Song.artistID AND Album.id = Song.albumID", playlistID)
    results = cur.fetchall()
    cur.close()
    return render_template('playlist.html', title='View', candelete=candelete, name=name, results=results, playlistid=playlistID, playlistType='public')

# view specific private playlist page
@app.route('/privateview')
@login_required
def ViewPrivate():
    # display all songs in the selected playlist and allow deletion if from the account page
    candelete= request.args.get('candelete')
    playlistID=request.args.get('playlistID')
    name=request.args.get('name')
    cur = conn.cursor()
    cur.execute("SELECT * FROM PrivateSongs WHERE playlistID = %s", playlistID)
    results = cur.fetchall()
    cur.execute("SELECT PrivateSongs.songid, Song.title, Artist.name, Album.title FROM PrivateSongs, Song, Artist, Album WHERE PrivateSongs.playlistID = %s AND PrivateSongs.songid = Song.id AND Artist.id = Song.artistID AND Album.id = Song.albumID", playlistID)
    results = cur.fetchall()
    cur.close()
    return render_template('playlist.html', title='Private View', candelete=candelete, name=name, results=results, playlistid=playlistID, playlistType='private')

# delete song from playlist page
@app.route('/deletesong', methods=['GET', 'POST'])
@login_required
def DeleteSong():
    # gather all data from previous html page
    candelete=request.args.get('candelete')
    songID= request.args.get('songID')
    playlistID= request.args.get('playlistid')
    playlistType= request.args.get('playlistType')
    name=request.args.get('name')
    # if the song is being deleted from a public playlist
    if playlistType == 'public':
        # delete the specified song from the specified playlist then return the remaining playlists to the user
        cur=conn.cursor()
        cur.execute("delete from PublicSongs where playlistID=%s and songid=%s", (playlistID, songID))
        conn.commit()
        cur.execute("SELECT PublicSongs.songid, Song.title, Artist.name, Album.title FROM PublicSongs, Song, Artist, Album WHERE PublicSongs.playlistID = %s AND PublicSongs.songid = Song.id AND Artist.id = Song.artistID AND Album.id = Song.albumID", playlistID)
        results = cur.fetchall()
        # if there are no more songs on the playlist, delete it and return to the account page
        if not results:
            cur.execute("delete from PublicPlaylist where id=%s ", playlistID)
            conn.commit()
            cur.close()
            return redirect(url_for('Account'))
        cur.close()
        return render_template('playlist.html', title='View', candelete=candelete, name=name, results=results, playlistid=playlistID, playlistType='public')
    # if the song is being deleted from a private playlist
    elif playlistType == 'private':
        # delete the specified song from the specified playlist then return the remaining playlists to the user
        cur=conn.cursor()
        cur.execute("delete from PrivateSongs where playlistID=%s and songid=%s", (playlistID, songID))
        conn.commit()
        cur.execute("SELECT PrivateSongs.songid, Song.title, Artist.name, Album.title FROM PrivateSongs, Song, Artist, Album WHERE PrivateSongs.playlistID = %s AND PrivateSongs.songid = Song.id AND Artist.id = Song.artistID AND Album.id = Song.albumID", playlistID)
        results = cur.fetchall()
        # if there are no more songs on the playlist, delete it and return to the account page
        if not results:
            cur.execute("delete from PrivatePlaylist where id=%s ", playlistID)
            conn.commit()
            cur.close()
            return redirect(url_for('Account'))
        cur.close()
        return render_template('playlist.html', title='View', candelete=candelete, name=name, results=results, playlistid=playlistID, playlistType='private')
    # error handle
    else:
        flash(f"Failed to delete your song from { name }. Try again.", 'info')
        return redirect(url_for('Account'))

# create public playlists page
@app.route('/public', methods=['GET', 'POST'])
@login_required
def PublicPlaylist():
    # get songID of the song being added to a playlist
    songID= request.args.get('songID')
    # get all playlist form data
    form = PlaylistForm()
    # done on a POST
    if form.validate_on_submit():
        # check if a playlist with the given name already exists
        userid = current_user.get_id()
        cur=conn.cursor()
        cur.execute("SELECT id FROM PublicPlaylist WHERE name = %s", form.playlistName.data)
        results = cur.fetchall()
        # Don't allow multiple playlists by the same user to have the same name
        if(len(results) > 0):
            flash("Playlist with that name already exists")
            return redirect(url_for('Search'))
        # Create the new playlist and add the song to it
        cur.execute("INSERT INTO PublicPlaylist(name, datecreated, userid, id) VALUES(%s, %s, %s, NULL)", (form.playlistName.data, date.today(), userid))
        conn.commit()
        cur.execute("INSERT INTO PublicSongs(id, userid, songid, playlistID) VALUES(NULL, %s, %s, LAST_INSERT_ID())", (userid, songID))
        conn.commit()
        cur.close()
        return redirect(url_for('Search'))
    # done on a GET
    cur = conn.cursor()
    # show the user all of their current public playlists
    cur.execute("SELECT DISTINCT name FROM PublicPlaylist where userid=%s", (current_user.get_id()))
    results = cur.fetchall()
    cur.close()
    reqtype = 'Public'
    return render_template('user.html', form=form, title='User', results=results, songID=songID, reqtype=reqtype)

# create private playlists page
@app.route('/private', methods=['GET', 'POST'])
@login_required
def PrivatePlaylist():
    # get songID of the song being added to a playlist
    songID= request.args.get('songID')
    # get all playlist form data
    form = PlaylistForm()
    # done on a POST
    if form.validate_on_submit():
        # check if a playlist with the given name already exists
        userid = current_user.get_id()
        cur=conn.cursor()
        cur.execute("SELECT id FROM PrivatePlaylist WHERE name = %s", form.playlistName.data)
        results = cur.fetchall()
        # Don't allow multiple playlists by the same user to have the same name
        if(len(results) > 0):
            flash("Playlist with that name already exists")
            return redirect(url_for('Search'))
        # Create the new playlist and add the song to it
        cur.execute("INSERT INTO PrivatePlaylist(name, datecreated, userid, id) VALUES(%s, %s, %s, NULL)", (form.playlistName.data, date.today(), userid))
        conn.commit()
        cur.execute("INSERT INTO PrivateSongs(id, userid, songid, playlistID) VALUES(NULL, %s, %s, LAST_INSERT_ID())", (userid, songID))
        conn.commit()
        cur.close()
        return redirect(url_for('Search'))
    # done on a GET
    cur = conn.cursor()
    # show the user all of their current private playlists
    cur.execute("SELECT DISTINCT name FROM PrivatePlaylist where userid=%s", (current_user.get_id()))
    results = cur.fetchall()
    cur.close()
    reqtype = 'Private'
    return render_template('user.html', form=form, title='User', results=results, songID=songID, reqtype=reqtype)

# add a song to an existing public playlist
@app.route('/addpublic')
@login_required
def AddPublicSong():
    # gather all information from previous page
    playlist = request.args.get('playlist')
    userid = current_user.get_id()
    songID = request.args.get('songID')
    # get the id of the playlist being inserted into
    cur=conn.cursor()
    cur.execute("SELECT id FROM PublicPlaylist WHERE name = %s", playlist)
    results = cur.fetchone()
    # check if song already exists in playlist
    cur.execute("SELECT PublicSongs.songid FROM PublicSongs, PublicPlaylist WHERE PublicSongs.songid = %s and PublicPlaylist.name = %s", (songID, playlist))
    check = cur.fetchone()
    # don't allow the same song to be inserted into the same playlist
    if check != None:
        flash(f"The song you've selected is already in { playlist }", 'info')
        cur.close()
        return redirect(url_for('Search'))
    else:
        # insert the new song into the playlist
        cur.execute("INSERT INTO PublicSongs(id, userid, songid, playlistID) VALUES(NULL, %s, %s, %s)", (userid, songID, results[0]))
        conn.commit()
        cur.close()
        return redirect(url_for('Search'))

# add a song to an existing private playlist
@app.route('/addprivate')
@login_required
def AddPrivateSong():
    # gather all information from previous page
    playlist = request.args.get('playlist')
    userid = current_user.get_id()
    songID = request.args.get('songID')
    # get the id of the playlist being inserted into
    cur=conn.cursor()
    cur.execute("SELECT id FROM PrivatePlaylist WHERE name = %s", playlist)
    results = cur.fetchone()
    # check if song already exists in playlist
    cur.execute("SELECT PrivateSongs.songid FROM PrivateSongs, PrivatePlaylist WHERE PrivateSongs.songid = %s and PrivatePlaylist.name = %s", (songID, playlist))
    check = cur.fetchone()
    # don't allow the same song to be inserted into the same playlist
    if check != None:
        cur.close()
        flash(f"The song you've selected is already in { playlist }", 'info')
        return redirect(url_for('Search'))
    else:
        # insert the new song into the playlist
        cur.execute("INSERT INTO PrivateSongs(id, userid, songid, playlistID) VALUES(NULL, %s, %s, %s)", (userid, songID, results[0]))
        conn.commit()
        cur.close()
        return redirect(url_for('Search'))

# logout page
@app.route('/logout')
def Logout():
    # use loginmanager to logout
    logout_user()
    return redirect(url_for('Login'))

# handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', title='404')