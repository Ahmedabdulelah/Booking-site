@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  error = False
  try:
    artist = Artist.query.get(artist_id)
    if artist is None:
      flash('Artist not found!')
      return redirect(url_for('index'))
    else:
      db.session.delete(artist)
      db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    # db.session.close()
    if error:
      flash('An error occurred. Artsit could not be deleted')
    else:
      flash('Artist successfully deleted')
    return redirect(url_for('index'))
  return None          


@app.route('/artists/<int:artist_id>/delete',methods=['POST'])
def delete_artists(artist_id):
  artist = Artist.query.get(artist_id)
  if artist:
    db.session.delete(artist)
    db.session.commit()
    flash('Artist deleted successfuly','success')
  else:
    flash('Artist not found','error')
    return redirect(url_for('index'))  
