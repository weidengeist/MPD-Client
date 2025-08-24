# -*- coding: utf-8 -*-
# line above is necessary for symbols », «, and more

import mpd

#client = mpd.MPDClient()
#client.connect('localhost', 6666)

class newClient(mpd.MPDClient):
  def __init__(self):
    super().__init__()
    #self = mpd.MPDClient()
    self.connect('localhost', 6666)

  def getArtistList(self):
    artists = self.list('artist')
    #artists.remove('')
    print(artists)

  def getAlbumList(client, artist):
    fullList = sorted(client.find("artist", artist), key=lambda x: x["date"])
    if len(fullList) == 0:
      return
    if not 'date' in fullList[0]:
      fullList[0]['date'] = "no date available"
    if not 'album' in fullList[0]:
      fullList[0]['album'] = "no album available"
    reducedList = {0: fullList[0]['date']+": "+fullList[0]['album']}
    for entry in range(1, len(fullList)):
      if not 'date' in fullList[entry]:
        fullList[entry]['date'] = "no date available"
      if not 'album' in fullList[entry]:
        fullList[entry]['album'] = "no album available"
      if reducedList[len(reducedList)-1] != fullList[entry]['date']+": "+fullList[entry]['album']:
        reducedList[len(reducedList)] = fullList[entry]['date']+": "+fullList[entry]['album']
    return reducedList

  def getTrackList(self, artist, album):
    data = self.find('artist', artist, 'album', album)
    print(data)
    trackList = {}
    for track in range(0, len(data)):
      trackList[track] = data[track]['title']
    return trackList

  def fileInfo(self, uri):
    print(self.lsinfo(uri))

c = newClient()
#c.getArtistList()
#print(c.playlistinfo())

#print("TAGTYPES: ", c.send("tagtypes"))
#print(c.channels())
#print(c.sendmessage("localhost", "tagtypes"))

#def getArtistList(client):
#  artists = client.list('artist')
#  artists.remove('')
#  return artists



#def getCurrentPlaylist():
print(c.find("artist", "Milne"))





c.getTrackList("Can Bardd", "Devoured by the Oak")

#liste = c.playlistinfo()
#for s in liste:
#  print(s)
