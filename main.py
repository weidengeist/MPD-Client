# -*- coding: utf-8 -*-
# The line above is necessary for symbols », «, and more.

# General functionality modules.
from os import path as sysPath
from os import mkdir
from os import system as sysExec
import re
import socket
import subprocess
import sys # Enables using command line arguments.
import time

# GTK GUI.
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk

from gi.repository import GLib # For GLib.timeout_add.
from gi.repository.GdkPixbuf import Pixbuf
from gi.repository import Pango

# Get the base directory. This is needed for evaluating symbolic links to the original program path.
BASEDIR = sysPath.join("/".join(sysPath.realpath(sys.argv[0]).split("/")[0:-1]))


#############################
# General helper functions. #
#############################

def secondsToTime(seconds):
  timeList = [0, 0, 0, seconds]
  if timeList[3] > 0:
    timeList[2] = (timeList[3] - timeList[3] % 60) / 60
    timeList[3] = timeList[3] % 60
  if timeList[2] > 0:
    timeList[1] = (timeList[2] - timeList[2] % 60) / 60
    timeList[2] = timeList[2] % 60
  if timeList[1] > 0:
    timeList[0] = (timeList[1] - timeList[1] % 24) / 24
    timeList[1] = timeList[1] % 24
  
  timeString = "" if timeList[0] == 0 else str(int(timeList[0])) + " d, " 
  timeString = "" if timeString == "" and timeList[1] == 0 else timeString + ("0" if len(str(int(timeList[1]))) == 1 else "") + str(int(timeList[1])) + ":"
  timeString = timeString + ("0" if len(str(int(timeList[2]))) == 1 else "") + str(int(timeList[2])) + ":"
  timeString = timeString + ("0" if len(str(int(timeList[3]))) == 1 else "") + str(int(timeList[3]))
  
  return timeString



##################
# Lyrics editor. #
##################
class lyricsEditor(Gtk.Window):
  def __init__(self, parent):
    super().__init__()

    self.lyricsFilePath = ""
    self.songPath = ""

    self.set_default_icon_name("mpd")
    self.set_title("Edit lyrics")
    print(parent.get_size())
    self.set_default_size(1/3 * parent.get_size().width, 0.8 * parent.get_size().height)
    self.set_transient_for(parent)
    self.set_position(4)
    self.connect("destroy", self.quit, parent)

    self.lyricsFilePathLabel = Gtk.Label()
    self.lyricsFilePathLabel.set_line_wrap(True)
    self.lyricsFilePathLabel.set_line_wrap_mode(0)
    self.lyricsFilePathLabel.set_xalign(0)

    monospaceButton = Gtk.ToggleButton()
    monospaceButton.set_label("Monospace font")
    monospaceButton.set_margin_bottom(5)
    monospaceButton.connect("toggled", self.setMonospaceFont)

    abortButton = Gtk.Button()
    abortButton.set_label("Cancel")
    abortButton.set_image(Gtk.Image.new_from_icon_name("gtk-cancel", 4))
    abortButton.connect("clicked", self.abortClicked)

    saveAndQuitButton = Gtk.Button()
    saveAndQuitButton.set_label("Save and close")
    saveAndQuitButton.set_image(Gtk.Image.new_from_icon_name("gtk-save", 4))
    saveAndQuitButton.connect("clicked", self.saveAndQuitClicked, parent)

    controlsBox = Gtk.HBox()
    controlsBox.set_spacing(5)
    controlsBox.set_margin_bottom(5)
    controlsBox.set_margin_top(5)
    controlsBox.set_homogeneous(True)
    controlsBox.pack_start(abortButton, True, True, 0)
    controlsBox.pack_start(saveAndQuitButton, True, True, 0)

    self.textEditorEntry = Gtk.TextView()
    
    self.textEditorStyle = Gtk.CssProvider()
    self.textEditorStyleContext = self.textEditorEntry.get_style_context()
    self.textEditorStyleContext.add_provider(self.textEditorStyle, Gtk.STYLE_PROVIDER_PRIORITY_USER)
    
    self.getCurrentSongLyrics(parent)
    
    textEditorEntryPath = self.textEditorEntry.get_path()
    textEditorEntryStyleContext = self.textEditorEntry.get_style_context()
    font = textEditorEntryStyleContext.get_font(0)
    print(textEditorEntryStyleContext, "———", font.get_family(), "———", font.get_size(), "———", Pango.SCALE, "———", font.get_variant())
    font.set_absolute_size(16)
    print(font.get_size())
    #self.textEditorEntry.style_updated()
    #a = self.textEditorEntry.get_style_context()
    #f = a.get_font(0)
    #print(textEditorEntryPath, "———", a, "———", f.get_family(), "———", f.get_size(), "———", Pango.SCALE, "———", f.get_variant())
    
    self.textEditorScroller = Gtk.ScrolledWindow()
    self.textEditorScroller.add(self.textEditorEntry)
    #self.textEditorMouseover = False
    self.connect("key_press_event", self.keyPressed)
    self.textEditorScroller.connect("enter-notify-event", self.printEnter)
    #self.textEditor.connect("leave-notify-event", self.printLeave)
    self.textEditorScroller.connect("scroll-event", self.scrollEvent)
    #self.textEditor.connect("motion_notify_event", self.printLeave)
    #self.textEditorEntry.props.events = 4096+8192 # Register mouse enter and mouse leave events.
    

    self.mainBox = Gtk.VBox()
    self.mainBox.set_margin_top(5)
    self.mainBox.set_margin_start(5)
    self.mainBox.set_margin_end(5)
    self.mainBox.set_margin_bottom(5)
    
    self.mainBox.pack_start(self.lyricsFilePathLabel, False, False, 0)
    self.mainBox.pack_start(controlsBox, False, False, 0)
    self.mainBox.pack_start(monospaceButton, False, False, 0)
    self.mainBox.pack_start(self.textEditorScroller, True, True, 0)

    self.add(self.mainBox)

    self.textEditorEntry.grab_focus()
    
    self.show_all()
    

  def printEnter(self, a, b):
    print("Entered!")
    #self.textEditorMouseover = True
    #self.textEditor.set_monospace(True)


  def printLeave(self, a, b):
    self.genericCounter += 1
    print(self.genericCounter)
    self.textEditorMouseover = False


  def setMonospaceFont(self, button):
    self.textEditorEntry.set_monospace(True if button.get_active() else False)


  def keyPressed(self, a, b):
    print(a, b)


  def abortClicked(self, button):
    self.destroy()


  def saveAndQuitClicked(self, button, parent):
    baseDir = parent.mpd.musicDirectory + "/" + "/".join(self.songPath.split("/")[0:-1])
    if not sysPath.exists(baseDir + "/lyrics"):
      mkdir(baseDir + "/lyrics")
    textBuffer = self.textEditorEntry.get_buffer()
    textRange = textBuffer.get_bounds()
    lyrics = textBuffer.get_text(textRange.start, textRange.end, True)
    f = open(self.lyricsFilePath, "w")
    f.write(lyrics)
    f.close()
    parent.findAndSetLyrics(parent.currentSongInfo_lyrics, self.songPath)
    self.destroy()


  def getCurrentSongLyrics(self, parent):
    currentSong = parent.mpd.send("currentsong")
    if len(currentSong) == 0:
      currentSong = parent.mpd.send("playlistinfo")

    if len(currentSong) > 0:
      self.songPath = re.findall("file: ([^\n]+)", currentSong)[0]
      fullSongPath = parent.mpd.musicDirectory + "/" + self.songPath
      songFileName = re.findall(r"(.*)\..+", (self.songPath.split("/"))[-1])[0]
      searchDirectory = re.findall(r"(.*)/.*", fullSongPath)[0]
      self.lyricsFilePath = searchDirectory + "/lyrics/" + songFileName
      self.lyricsFilePathLabel.set_markup("Lyrics file: <span font=\"Monospace\">" + self.lyricsFilePath + "</span>")
      if sysPath.exists(self.lyricsFilePath):
        f = open(self.lyricsFilePath)
        lyrics = f.read()
        f.close()
        self.textEditorEntry.set_buffer(Gtk.TextBuffer(text = lyrics))
        self.textEditorEntry:do_move_cursor(Gtk.MovementStep(3), -3, False)


  def scrollEvent(self, scrolledWindow, ScrollEvent):
    # Bitwise »and«: Check, if the state contains the Ctrl key modifier.
    if (ScrollEvent.state & Gdk.ModifierType.CONTROL_MASK) == Gdk.ModifierType.CONTROL_MASK:
      # Deactivate the scrolling.
      scrolledWindow.stop_emission_by_name("scroll-event")
      fontSize = round(self.textEditorStyleContext.get_property("font-size", 0)) - int(ScrollEvent.delta_y)
      if fontSize >= 4 and fontSize <= 144: 
        newStyleString = "textview{font-size: " + str(fontSize) + "px}"
        self.textEditorStyle.load_from_data(newStyleString.encode())


  def quit(self, _, parent):
    parent.editLyricsButton.handler_unblock(parent.editLyricsButton_connectID)
    

############################
# MPD backend for queries. #
############################

class mpdClient():  
  def __init__(self):
    configFile = sysPath.expanduser("~") + "/.mpd/mpd.conf"
    if not sysPath.exists(configFile):
      configFile = "/etc/mpd/mpd.conf"
    
    handle = open(configFile, "r")
    contents = handle.read()
    self.musicDirectory = re.findall("[\n]?music_directory[ \t]*\"([^\n]+)\"", contents)[0]
    self.host = re.findall("[\n]?bind_to_address[ \t]*\"([^\n]+)\"", contents)[0]
    self.port = int(re.findall("[\n]?port[ \t]*\"([0-9]+)\"", contents)[0])
    handle.close()


  def send(self, command):
    self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.connection.connect((self.host, self.port))
    self.connection.send((command + "\n").encode())
    response = b''
    while 1:
      try:
        response += self.connection.recv(1024)
        responseEnd = re.compile(".*OK\n$", re.MULTILINE|re.DOTALL)
        if re.match(responseEnd, response.decode('utf-8', 'ignore')):
          self.connection.close()
          return re.sub("^OK MPD [0-9.]+\n?", "", re.sub("[\n]?OK\n$", "", response.decode()))
      except:
        self.connection.close()
        break


############
# MPD GUI. #
############

class mpdGUI(Gtk.Window):
  def __init__(self):
    super().__init__()

    self.set_default_icon_name("mpd")
    self.set_default_size(890, 200)

    self.mpd = mpdClient()

    self.mpd.send("tagtypes all")
    print(self.mpd.send("tagtypes"))

    windowTitle = ""
    currentPlaylist = re.findall("[0-9]+:file: [^\n]+", self.mpd.send("playlist"))
    if len(currentPlaylist) > 0:
      currentSong = self.mpd.send("currentsong")
      if len(currentSong) == 0:
        firstPlaylistFile = re.findall("^[0-9]+:file: ([^\n]+)", currentPlaylist[0])[0]
        currentSong = self.mpd.send("find file \"" + firstPlaylistFile + "\"")
        self.currentSongPos = 0
      else:
        self.currentSongPos = int(re.findall("[\n]?Pos: ([^\n]+)", currentSong)[0])
      artist = re.findall("[\n]?Artist: ([^\n]+)", currentSong)[0]
      title = re.findall("[\n]?Title: ([^\n]+)", currentSong)[0]
      windowTitle = "»" + title + "«" + " by " + artist
    else:
      windowTitle = "Playlist is empty"
      self.currentSongPos = -1

    self.set_title(windowTitle)

    # Get the system default font size. Needed for varying font sizes in info panels.
    f = open(sysPath.expanduser("~") + "/.config/gtk-3.0/settings.ini", "r")
    self.defaultFontSize = int(re.findall("gtk-font-name=.*?([0-9]+)\n", f.read())[0])
    f.close()


    ####################################
    # Composing the library tree view. #
    ####################################

    # Artist, Album, Year/Date; all columns are strings.
    self.libraryTreeStore = Gtk.ListStore(str, str, str)
    
    # Initialize the tree view with the model generated above.
    self.libraryTreeView = Gtk.TreeView(model = self.libraryTreeStore)
    self.libraryTreeView.get_selection().set_mode(Gtk.SelectionMode(3))
    self.libraryTreeView.set_rubber_banding(True)
    
    # Create the columns for the tree view.
    renderer = Gtk.CellRendererText()
    renderer.set_alignment(0, 0)
    column = Gtk.TreeViewColumn("Artist", cell_renderer = renderer, text = 0)
    column.set_resizable(True)
    self.libraryTreeView.append_column(column)

    renderer = Gtk.CellRendererText()
    renderer.props.wrap_width = 200
    renderer.props.wrap_mode = Pango.WrapMode(2)
    column = Gtk.TreeViewColumn("Album", cell_renderer = renderer, text = 1)
    column.set_resizable(True)
    self.libraryTreeView.append_column(column)
  
    renderer = Gtk.CellRendererText()
    renderer.set_alignment(1.0, 0)
    column = Gtk.TreeViewColumn("Year", cell_renderer = renderer, text = 2)
    column.set_expand(False)
    self.libraryTreeView.append_column(column)

    self.libraryTreeView_connectID = self.libraryTreeView.get_selection().connect("changed", self.libraryEntryClicked)
   
    
    #############################################################
    # Composing the tree view that lists the songs of an album. #
    #############################################################

    # Track, Title, Duration; all columns are strings.
    self.albumSongsTreeStore = Gtk.ListStore(str, str, str)
  
    # Initialize the tree view with the model generated above.
    self.albumSongsTreeView = Gtk.TreeView(model = self.albumSongsTreeStore)
    
    # Create the columns for the tree view.
    column = Gtk.TreeViewColumn("Track", cell_renderer = Gtk.CellRendererText(xalign = 1.0), text = 0)
    column.set_resizable(True)
    self.albumSongsTreeView.append_column(column)

    column = Gtk.TreeViewColumn("Title", cell_renderer = Gtk.CellRendererText(), text = 1)
    column.set_resizable(True)
    self.albumSongsTreeView.append_column(column)
  
    column = Gtk.TreeViewColumn("Duration", cell_renderer = Gtk.CellRendererText(xalign = 1.0), text = 2)
    self.albumSongsTreeView.append_column(column)


    ############################################################
    # Composing the tree view that shows the current playlist. #
    ############################################################

    # Track, Title, Duration; all columns are strings.
    self.playlistTreeStore = Gtk.ListStore(str, str, str)

    # Initialize the tree view with the model generated above.
    self.playlistTreeView = Gtk.TreeView(model = self.playlistTreeStore)
    self.playlistTreeView.get_selection().set_mode(Gtk.SelectionMode(3))
    self.playlistTreeView.set_rubber_banding(True)

    #self.playlistTreeView.connect("key_press_event", self.keyPressed_playlist)
    
    # Create the columns for the tree view.
    column = Gtk.TreeViewColumn("Track", cell_renderer = Gtk.CellRendererText(xalign = 1.0), markup = 0)
    column.set_resizable(True)
    column.set_alignment(1.0)
    self.playlistTreeView.append_column(column)

    column = Gtk.TreeViewColumn("Title", cell_renderer = Gtk.CellRendererText(), markup = 1)
    column.set_resizable(True)
    column.set_expand(True)
    self.playlistTreeView.append_column(column)
  
    column = Gtk.TreeViewColumn("Duration", cell_renderer = Gtk.CellRendererText(xalign = 1.0), markup = 2)
    column.set_expand(False)
    self.playlistTreeView.append_column(column)

    self.playlistTreeView.connect("row-activated", self.playlistEntryDoubleclicked)
    

    #####################################################
    # Setting the notebook (tabs Library and Playlist). #
    #####################################################

    self.notebook = Gtk.Notebook()


    # Defining the Library page contents.
    self.pageLibrary = Gtk.VBox()
    
    box = Gtk.HBox()
    box.set_spacing(0.5 * self.defaultFontSize)
    box.set_margin_top(0.5 * self.defaultFontSize)

    libraryHeaderGrid = Gtk.Grid()
    libraryHeaderGrid.set_column_spacing(10)
    libraryHeaderGrid.set_row_spacing(0.5 * self.defaultFontSize)
    libraryHeaderGrid.set_margin_top(0.5 * self.defaultFontSize)

    label = Gtk.Label(label = "Library mode:")
    label.set_xalign(0)
    self.libraryModeBox = Gtk.ComboBoxText()
    self.libraryModeBox.append(None, "Artist tag")
    self.libraryModeBox.append(None, "File system")
    self.libraryModeBox.set_active(0)

    libraryHeaderGrid.attach(label, 1, 1, 1, 1)
    libraryHeaderGrid.attach(self.libraryModeBox, 2, 1, 1, 1)

    label = Gtk.Label(label = "Genre filter:")
    label.set_xalign(0)
    self.genreFilterBox = Gtk.ComboBoxText()
    self.genreFilterBox.set_hexpand(True)
    self.populateGenreFilter() # Do this before connecting the »changed« signal to prevent unresolvable effects on the library.
    self.genreFilterBox_connectID = self.genreFilterBox.connect("changed", self.genreFilterChanged)
    #box.pack_start(label, False, False, 0)
    #box.pack_start(self.genreFilterBox, True, True, 0)

    libraryHeaderGrid.attach(label, 1, 2, 1, 1)
    libraryHeaderGrid.attach(self.genreFilterBox, 2, 2, 1, 1)

    self.pageLibrary.pack_start(libraryHeaderGrid, False, False, 0)

    scrolledWindow = Gtk.ScrolledWindow()
    scrolledWindow.add(self.libraryTreeView)

    self.pageLibrary.pack_start(scrolledWindow, True, True, 0)

    buttonBox = Gtk.HBox()
    
    button = Gtk.Button.new_from_icon_name("list-add", 4)
    button.set_tooltip_text("Add all selected albums to playlist")
    button.connect("clicked", self.buttonAddAlbumsClicked)
    buttonBox.pack_start(button, False, False, 0)
    
    button = Gtk.Button.new_from_icon_name("edit-find-replace", 4)
    button.set_tooltip_text("Replace current playlist with selected albums")
    button.connect("clicked", self.buttonReplacePlaylistClicked, self.libraryTreeView, self.playlistTreeStore, self.playlistTreeView)
    buttonBox.pack_start(button, False, False, 0)
    
    self.updateLibraryButton = Gtk.Button.new_from_icon_name("gtk-refresh", 4)
    self.updateLibraryButton.set_tooltip_text("Update library")
    self.updateLibraryButton.connect("clicked", self.buttonUpdateLibraryClicked)
    buttonBox.pack_start(self.updateLibraryButton, False, False, 0)
    
    button = Gtk.Button.new_from_icon_name("edit-find", 4)
    button.set_tooltip_text("Advanced song search … [Work in progress]")
    button.connect("clicked", self.buttonFindSongsClicked)
    buttonBox.pack_start(button, False, False, 0)
    
    self.libraryInfo = Gtk.Label()
    self.libraryInfo.set_hexpand(True)
    self.libraryInfo.set_xalign(1)
    self.libraryInfo.set_yalign(0.5)
    buttonBox.pack_start(self.libraryInfo, False, True, 0)

    self.pageLibrary.pack_start(buttonBox, False, False, 0)

    self.notebook.append_page(self.pageLibrary, Gtk.Label(label = "Library"))


    # Composing the playlist elements on the notebook page.

    scrolledWindow = Gtk.ScrolledWindow()
    scrolledWindow.add(self.playlistTreeView)

    buttonBox = Gtk.HBox()

    button = Gtk.Button.new_from_icon_name("gtk-go-up", 4)
    button.set_tooltip_text("Move selected items up")
    button.connect("clicked", self.buttonMovePlaylistItemsUp, self.playlistTreeView, self.playlistTreeStore)
    buttonBox.pack_start(button, False, False, 0)

    button = Gtk.Button.new_from_icon_name("gtk-go-down", 4)
    button.set_tooltip_text("Move selected items down")
    button.connect("clicked", self.buttonMovePlaylistItemsDown, self.playlistTreeView, self.playlistTreeStore)
    buttonBox.pack_start(button, False, False, 0)

    button = Gtk.Button.new_from_icon_name("list-remove", 4)
    button.set_tooltip_text("Delete selected items from the playlist")
    button.connect("clicked", self.buttonDeletePlaylistItems, self.playlistTreeView, self.playlistTreeStore)
    buttonBox.pack_start(button, False, False, 0)

    self.repeatButton = Gtk.ToggleButton()
    self.repeatButton.set_image(Gtk.Image.new_from_icon_name("media-playlist-repeat", 4))
    self.repeatButton.set_tooltip_text("Repeat the playlist")
    self.repeatButton.connect("toggled", self.buttonToggleRepeat)
    buttonBox.pack_start(self.repeatButton, False, False, 0)

    self.playlistPlaytimeInfo = Gtk.Label()
    self.playlistPlaytimeInfo.set_hexpand(True)
    self.playlistPlaytimeInfo.set_xalign(1)
    self.playlistPlaytimeInfo.set_yalign(0.5)
    #self.playlistPlaytimeInfo.connect("key-press-event", self.showSomething)

    buttonBox.pack_start(self.playlistPlaytimeInfo, False, True, 0)

    self.pagePlaylist = Gtk.VBox()
    self.pagePlaylist.pack_start(scrolledWindow, True, True, 0)
    self.pagePlaylist.pack_start(buttonBox, False, False, 0)
    self.notebook.append_page(self.pagePlaylist, Gtk.Label(label = "Playlist"))


    self.notebook.connect("switch_page", self.notebookPageSwitched)
    
    
    ############################################################################
    # Setting the center panel (album cover art and playback control buttons). #
    ############################################################################

    self.coverArt = Gtk.Image()
    self.coverArt.set_margin_start(5)
    self.coverArt.set_margin_end(5)
    self.coverArt.set_margin_top(5)
    self.coverArt.set_margin_bottom(5)
    self.setCoverArt(self.coverArt, sysPath.join(BASEDIR, "noCover.png"))

    albumFrame = Gtk.Frame()
    albumFrame.add(self.coverArt)

    buttonBox = Gtk.HBox()
    
    button = Gtk.Button.new_from_icon_name("media-skip-backward", 4)
    button.connect("clicked", self.buttonPlaybackPreviousClicked)
    button.set_size_request(Gtk.IconSize.lookup(4).width + self.defaultFontSize, Gtk.IconSize.lookup(4).height + self.defaultFontSize)
    buttonBox.pack_start(button, False, False, 0)

    button = Gtk.Button.new_from_icon_name("media-playback-stop", 4)
    button.connect("clicked", self.buttonPlaybackStopClicked)
    # Set each button’s size according to the theme’s button icon size (4).
    button.set_size_request(Gtk.IconSize.lookup(4).width + self.defaultFontSize, Gtk.IconSize.lookup(4).height + self.defaultFontSize)
    buttonBox.pack_start(button, False, False, 0)

    self.button_pause_play = Gtk.Button()
    self.button_pause_play.connect("clicked", self.buttonPlaybackStartClicked)
    self.button_pause_play.set_size_request(Gtk.IconSize.lookup(4).width + self.defaultFontSize, Gtk.IconSize.lookup(4).height + self.defaultFontSize)
    buttonBox.pack_start(self.button_pause_play, False, False, 0)

    button = Gtk.Button.new_from_icon_name("media-skip-forward", 4)
    button.connect("clicked", self.buttonPlaybackNextClicked)
    button.set_size_request(Gtk.IconSize.lookup(4).width + self.defaultFontSize, Gtk.IconSize.lookup(4).height + self.defaultFontSize)
    buttonBox.pack_start(button, False, False, 0)

    button = Gtk.ToggleButton()
    button.set_image(Gtk.Image.new_from_icon_name("audio-volume-muted", 4))
    button.connect("toggled", self.buttonMuteClicked)
    button.set_size_request(Gtk.IconSize.lookup(4).width + self.defaultFontSize, Gtk.IconSize.lookup(4).height + self.defaultFontSize)
    buttonBox.pack_start(button, False, False, 0)

    self.volumeScale = Gtk.Scale.new_with_range(0, 0, 100, 1)
    self.volumeScale.set_margin_start(10)
    self.volumeScale.set_increments(1,5)
    self.volumeScale.connect("change-value", self.volumeChanged)
    buttonBox.pack_start(self.volumeScale, True, True, 0)

    self.songProgressEventBox = Gtk.EventBox()
    self.songProgress = Gtk.ProgressBar()
    self.songProgress.set_show_text(True)
    self.songProgress.set_text("00:00/00:00")
        
    self.songProgressEventBox.add(self.songProgress)
    self.songProgressEventBox.connect("button-press-event", self.songProgressClicked)

    coverAndControlsBox = Gtk.VBox()
    coverAndControlsBox.pack_start(albumFrame, False, False, 0)
    coverAndControlsBox.pack_start(buttonBox, False, False, 0)
    coverAndControlsBox.pack_start(self.songProgressEventBox, False, False, 0)


    ####################################################
    # Setting the right panel (album info and lyrics). #
    ####################################################

    self.infoFrame = Gtk.Frame()

    infoFrame_vbox = Gtk.VBox()

    # Use the scroll universally. Info inside changes with the notebook tabs.
    self.infoScroll = Gtk.ScrolledWindow()
    self.infoScroll.set_propagate_natural_width(True)
    
    # Information on the currently selected album in the library view.
    self.albumInfo_heading = Gtk.Label()
    self.albumInfo_heading.set_xalign(0)
    self.albumInfo_heading.set_line_wrap(True)
    self.albumInfo_heading.set_margin_top(1.5 * self.defaultFontSize)
    self.albumInfo_heading.set_margin_start(1.5 * self.defaultFontSize)
    self.albumInfo_heading.set_margin_end(1.5 * self.defaultFontSize)
    
    self.albumInfo_subtitle = Gtk.Label()
    self.albumInfo_subtitle.set_xalign(0)
    self.albumInfo_subtitle.set_margin_start(1.5 * self.defaultFontSize)
    self.albumInfo_subtitle.set_margin_end(1.5 * self.defaultFontSize)

    self.albumInfo_tracklistGrid = Gtk.Grid()
    self.albumInfo_tracklistGrid.set_column_spacing(20)
    self.albumInfo_tracklistGrid.set_margin_top(self.defaultFontSize)
    self.albumInfo_tracklistGrid.set_margin_start(3 * self.defaultFontSize)
    self.albumInfo_tracklistGrid.set_margin_end(self.defaultFontSize)
    self.albumInfo_tracklistGrid.set_margin_bottom(1.5 * self.defaultFontSize)

    self.albumInfoBox = Gtk.VBox()
    self.albumInfoBox.pack_start(self.albumInfo_heading, False, False, 0)
    self.albumInfoBox.pack_start(self.albumInfo_subtitle, False, False, 0)
    self.albumInfoBox.pack_start(self.albumInfo_tracklistGrid, False, False, 0)

    # Information on the currently playing song in the playlist view.
    self.currentSongInfo_heading = Gtk.Label()
    self.currentSongInfo_heading.set_xalign(0)
    self.currentSongInfo_heading.set_line_wrap(True)
    self.currentSongInfo_heading.set_margin_top(1.5 * self.defaultFontSize)
    self.currentSongInfo_heading.set_margin_start(1.5 * self.defaultFontSize)
    self.currentSongInfo_heading.set_margin_end(1.5 * self.defaultFontSize)

    self.currentSongInfo_subtitle = Gtk.Label()
    self.currentSongInfo_subtitle.set_xalign(0)
    self.currentSongInfo_subtitle.set_line_wrap(True)
    self.currentSongInfo_subtitle.set_margin_start(1.5 * self.defaultFontSize)
    self.currentSongInfo_subtitle.set_margin_end(1.5 * self.defaultFontSize)

    self.currentSongInfo_lyrics = Gtk.Label()
    self.currentSongInfo_lyrics.set_line_wrap(True) # Wrap at words.
    self.currentSongInfo_lyrics.set_margin_top(2 * self.defaultFontSize)
    self.currentSongInfo_lyrics.set_margin_bottom(2 * self.defaultFontSize)
    self.currentSongInfo_lyrics.set_margin_start(1.5 * self.defaultFontSize)
    self.currentSongInfo_lyrics.set_margin_end(1.5 * self.defaultFontSize)    
    
    self.currentSongInfoBox = Gtk.VBox()
    self.currentSongInfoBox.pack_start(self.currentSongInfo_heading, False, False, 0)
    self.currentSongInfoBox.pack_start(self.currentSongInfo_subtitle, False, False, 0)
    self.currentSongInfoBox.pack_start(self.currentSongInfo_lyrics, False, False, 0)

    # Has to be realized separately, as it is not visible when the program is started.
    self.currentSongInfoBox.show_all()

    self.infoScroll.add(self.albumInfoBox)

    infoFrame_vbox.pack_start(self.infoScroll, True, True, 0)
    
    self.editTagsButton = Gtk.Button()
    self.editTagsButton.set_label("Edit tags")
    self.editTagsButton.set_margin_top(self.defaultFontSize)
    self.editTagsButton.props.halign = Gtk.Align.END
    self.editTagsButton.connect("clicked", self.openTagEditor)
    
    self.editLyricsButton = Gtk.Button()
    self.editLyricsButton.set_label("Edit lyrics")
    self.editLyricsButton.set_margin_top(self.defaultFontSize)
    self.editLyricsButton.props.halign = Gtk.Align.END
    self.editLyricsButton_connectID = self.editLyricsButton.connect("clicked", self.openLyricsEditor)
    
    infoFrame_vbox.pack_start(self.editTagsButton, False, False, 0)
    infoFrame_vbox.pack_start(self.editLyricsButton, False, False, 0)
    
    self.infoFrame.add(infoFrame_vbox)
    
    
    # mainBox contains all the window contents.
    self.mainBox = Gtk.HBox(margin = 10, spacing = 20, homogeneous = False)
    self.add(self.mainBox)

    self.mainBox.pack_start(self.notebook, True, True, 0)
    self.mainBox.pack_start(coverAndControlsBox, False, False, 0)
    self.mainBox.pack_start(self.infoFrame, True, True, 0)    

    self.connect("destroy", self.quit)

    self.show_all()
    
    ####################

    summary = self.populateLibrary(self.libraryTreeStore, self.libraryTreeView)
    self.setLibraryInfoText(summary)
    self.populatePlaylist(self.playlistTreeStore, self.playlistTreeView)
    self.updateSongProgress()

    status = self.mpd.send("status")
  
    currentVolume = re.findall("volume: ([0-9]+)", status)[0]
    self.volumeScale.set_value(int(currentVolume))

    state = re.findall("[\n]?state: ([^\n]+)", status)[0]
    if state == "play":
      self.button_pause_play.set_image(Gtk.Image.new_from_icon_name("media-playback-pause", 4))
    else:
      self.button_pause_play.set_image(Gtk.Image.new_from_icon_name("media-playback-start", 4))    

    repeatStatus = re.findall("[\n]?repeat: ([0-9])", status)[0]
    if repeatStatus == "1":
      self.repeatButton.set_active(True)

    # The right panel gets the same width as the left one.
    # Do this after populating the library and setting the cover art and the album info panel text to get the proper size.
    # The preferred info frame width might not be enough when scroll bars appear. Adding 1.5 times the font size as buffer.
    panelsMaxWidth = max(self.notebook.get_preferred_size()[1].width, self.infoFrame.get_preferred_size()[1].width + 1.5 * self.defaultFontSize)
    self.infoFrame.set_size_request(panelsMaxWidth, -1)
    self.notebook.set_size_request(panelsMaxWidth, -1)

    volumeScaleHeight = self.volumeScale.get_preferred_size()[1].height
    buttonsHeight = self.button_pause_play.get_preferred_size()[1].height
    for widget in buttonBox.get_children():
      if re.match(".*Button", widget.get_name()):
        widget.set_margin_top(volumeScaleHeight - buttonsHeight)

    vScrollbarWidth = self.infoScroll.get_vscrollbar().get_preferred_size()[1].width
    self.libraryInfo.set_margin_end(vScrollbarWidth)
    self.playlistPlaytimeInfo.set_margin_end(vScrollbarWidth)
    self.genreFilterBox.get_parent().set_margin_start(vScrollbarWidth)
    self.genreFilterBox.get_parent().set_margin_end(vScrollbarWidth)

    self.editLyricsButton.set_visible(False)

    self.updatePlaylistPlaytimeInfo_bgLoop()

    self.idleThread_player = subprocess.Popen(["python", sys.argv[0], "idle player"], 0)
    self.songChanged()

    currentWindowSize = self.get_size()
    prefSize = self.get_preferred_size()[0]
    print(prefSize.width, currentWindowSize)
    self.resize(prefSize.width, prefSize.height)
    #self.set_position(Gtk.WindowPosition.CENTER)
    Gtk.main()


  def showSomething(self, a, b, c):
    print("Show!")


  def keyPressed_playlist(self, a, b):
    print(a, b)
    

  def buttonAddAlbumsClicked(self, button):
    currentPlaylistLength = int(re.findall("[\n]?playlistlength: ([^\n]+)", self.mpd.send("status"))[0])
    model, paths = self.libraryTreeView.get_selection().get_selected_rows()  # The index of the latest selected entry.
    
    for i in range(0, len(paths)):
      iterator = model.get_iter(paths[i])
      
      artist = model.get_value(iterator, 0)  # Get value in column 0 (Artist).
      album = model.get_value(iterator, 1)  # Get value in column 1 (Album).
      year = model.get_value(iterator, 2)  # Get value in column 1 (Year).
      
      self.mpd.send("findadd artist \"" + artist + "\" album \"" + album + "\" date \"" + year + "\"")
    
    newPlaylist = self.mpd.send("playlistinfo")
    newPlaylistLength = int(re.findall("[\n]?playlistlength: ([^\n]+)", self.mpd.send("status"))[0])
    newTracks = re.findall("[\n]?Track: ([^\n]+)", newPlaylist)
    newTitles = re.findall("[\n]?Title: ([^\n]+)", newPlaylist)
    newDurations = re.findall("[\n]?Time: ([^\n]+)", newPlaylist)
    for i in range(currentPlaylistLength, newPlaylistLength):
      self.playlistTreeStore.append([newTracks[i], newTitles[i].replace("&", "&amp;"), secondsToTime(int(newDurations[i]))])


  def buttonDeletePlaylistItems(self, button, treeView, treeStore):
    model, paths = treeView.get_selection().get_selected_rows()
    if len(paths) > 0:
      for i in range(len(paths) - 1, -1, -1):
        index = paths[i].get_indices()[0]
        iterator = model.get_iter(paths[i])
        if index == self.currentSongPos and self.currentSongPos == len(treeStore) - 1:
          if len(treeStore) == 1:
            self.currentSongPos = -1
            self.mpd.send("stop")
          else:
            self.currentSongPos -= 1
            self.mpd.send("play " + str(self.currentSongPos))
        elif index < self.currentSongPos:
          self.currentSongPos -= 1
        treeStore.remove(iterator)
        self.mpd.send("delete " + str(index))


  def buttonFindSongsClicked(self, button, mpd):
    print("To do!")


  def buttonMovePlaylistItemsUp(self, button, treeView, treeStore):
    model, paths = treeView.get_selection().get_selected_rows()
    if len(paths) > 0 and paths[0].get_indices()[0] > 0:
      for i in range(0, len(paths)):
        index = paths[i].get_indices()[0]
        iterator_prev = model.get_iter(Gtk.TreePath.new_from_indices([index - 1]))
        iterator_this = model.get_iter(paths[i])
        treeStore.swap(iterator_prev, iterator_this)
        self.mpd.send("move " + str(index - 1) + " " + str(index))
        if index == self.currentSongPos:
          self.currentSongPos -= 1


  def buttonMovePlaylistItemsDown(self, button, treeView, treeStore):
    model, paths = treeView.get_selection().get_selected_rows()
    if len(paths) > 0 and paths[-1].get_indices()[0] < len(treeStore) - 1:
      for i in range(len(paths) - 1, -1, -1):
        index = paths[i].get_indices()[0]
        iterator_this = model.get_iter(paths[i])
        iterator_next = model.get_iter(Gtk.TreePath.new_from_indices([index + 1]))
        treeStore.swap(iterator_this, iterator_next)
        self.mpd.send("move " + str(index) + " " + str(index + 1))
        if index == self.currentSongPos:
          self.currentSongPos += 1


  def buttonMuteClicked(self, button):
    if button.get_active():
      self.mpd.send("setvol 0")
    else:
      self.mpd.send("setvol " + str(int(self.volumeScale.get_value())))
    

  def buttonPlaybackNextClicked(self, button):
    state = re.findall("[\n]?state: ([^\n]+)", self.mpd.send("status"))[0]
    if state != "stop":
      currentSongPos = int(re.findall("\nPos: ([^\n]+)", self.mpd.send("currentsong"))[0])
      currentPlaylistLength = int(re.findall("[\n]?playlistlength: ([^\n]+)", self.mpd.send("status"))[0])
      if currentSongPos == currentPlaylistLength - 1:
        self.mpd.send("play 0")
      else:
        self.mpd.send("next")


  def buttonPlaybackPreviousClicked(self, button):
    state = re.findall("[\n]?state: ([^\n]+)", self.mpd.send("status"))[0]
    if state != "stop":
      self.mpd.send("previous")


  def buttonPlaybackStartClicked(self, button):
    state = re.findall("[\n]?state: ([^\n]+)", self.mpd.send("status"))[0]
    if state == "play":
      self.mpd.send("pause")
      button.set_image(Gtk.Image.new_from_icon_name("media-playback-start", 4))
    else:
      self.mpd.send("play")
      button.set_image(Gtk.Image.new_from_icon_name("media-playback-pause", 4))
      self.updateSongProgress()


  def buttonPlaybackStopClicked(self, button):
    self.mpd.send("stop")
    currentSong = self.mpd.send("currentsong")
    self.songProgress.set_fraction(0)
    self.songProgress.set_text(str(secondsToTime(0)) + re.sub("^[^/]+", "", self.songProgress.get_text()))
    

  def buttonReplacePlaylistClicked(self, button, libraryTreeView, playlistTreeStore, playlistTreeView):
    status = self.mpd.send("status")
    state = re.findall("[\n]?state: ([^\n]+)", status)
    oldPlaylistLength = re.findall("[\n]?playlistlength: ([^\n]+)", status)[0]
    
    model, paths = libraryTreeView.get_selection().get_selected_rows() # The list of the selected albums.
    for i in range(0, len(paths)):
      iterator = model.get_iter(paths[i])
    
      artist = model.get_value(iterator, 0)  # Get value in column 0 (Artist).
      album = model.get_value(iterator, 1)  # Get value in column 1 (Album).
      year = model.get_value(iterator, 2)  # Get value in column 1 (Year).

      self.mpd.send("findadd artist \"" + artist + "\" album \"" + album + "\" date \"" + year + "\"")

    # Do not use self.mpd.send("clear") before adding the new songs or at all! 
    # Instead, delete the songs from the list explicitly after having added the new ones.
    # The »clear« command will otherwise stop the player.
    self.mpd.send("delete 0:" + oldPlaylistLength)

    playlistTreeStore.clear()
    self.populatePlaylist(playlistTreeStore, playlistTreeView)

    # state is here the state before the playlist replacement.
    if state == "Play":
      self.mpd.send("play")
    else:
      self.updateSongProgress()

    self.currentSongPos = 0
    self.updateGUIForChangedSong()


  def buttonToggleRepeat(self, button):
    if button.get_active():
      self.mpd.send("repeat 1")
    else:
      self.mpd.send("repeat 0")


  def buttonUpdateLibraryClicked(self, button):
    button.set_sensitive(False)
    self.libraryInfo.set_label("Updating …")
    self.mpd.send("update")
    self.checkLibraryUpdateFinished()
    

  def checkLibraryUpdateFinished(self):
    result = self.mpd.send("status")
    updatingKeyword = re.compile(".*updating_db: [0-9]+", re.MULTILINE|re.DOTALL)
    if re.match(updatingKeyword, result):
      GLib.timeout_add(500, self.checkLibraryUpdateFinished)
    else:
      self.updateLibraryButton.set_sensitive(True)
      self.libraryInfo.set_label("Library updated!")
      selectedGenreIndex = self.genreFilterBox.get_active()
      if selectedGenreIndex > 0:
        genre = self.genreFilterBox.get_active_text()
      else:
        genre = "NONE_SELECTED"
      newGenreList = self.mpd.send("list genre")
      newGenreIndex = 0
      genreRegex = re.compile(".*Genre: " + genre + "\n", re.MULTILINE|re.DOTALL)
      if re.match(genreRegex, newGenreList) or selectedGenreIndex == 0:
        print("Old Genre still available")
        if selectedGenreIndex > 0:
          span = int(re.findall(r"span=\([0-9]+, ([0-9]+)\)", str(re.match(genreRegex, newGenreList)))[0])
          newGenreIndex = len(re.findall("\n", newGenreList[0:span])) # The index in the new genre list that has to be selected.
      else:
        print("Old Genre no longer available")
      
      self.genreFilterBox.handler_block(self.genreFilterBox_connectID)
      self.genreFilterBox.remove_all()
      self.populateGenreFilter()
      self.genreFilterBox.set_active(newGenreIndex)
      self.genreFilterBox.handler_unblock(self.genreFilterBox_connectID)
      
      # Try to get the library treeview’s currently selected entry to restore the selection after the treeview renewal.
      # This situation occurs when updating the library and its treeview via this function.
      # Set a fallback value in case there has been no selected index before the update.
      visibleFirstIndex = 0
      visibleTopY = self.libraryTreeView.get_visible_rect().y
      model, paths = self.libraryTreeView.get_selection().get_selected_rows()
      if len(paths) > 0:
        selectedIndex = paths[0].get_indices()[0]
        visibleFirstIndex = self.libraryTreeView.get_visible_range()[0].get_indices()[0]
        iterator = model.get_iter(paths[0])
        selectedValues = [\
          model.get_value(iterator, 0),\
          model.get_value(iterator, 1),\
          model.get_value(iterator, 2)\
        ]

      self.libraryTreeView.get_selection().handler_block(self.libraryTreeView_connectID)
      #self.libraryTreeStore.clear()
      self.libraryTreeView.get_selection().handler_unblock(self.libraryTreeView_connectID)
      summary = self.populateLibrary(self.libraryTreeStore, self.libraryTreeView, genre, selectedValues)
      GLib.timeout_add(2000, self.setLibraryInfoText, summary)

      self.libraryTreeView.scroll_to_cell(Gtk.TreePath.new_from_indices([visibleFirstIndex+1]), None, False)
      

  def findAndSetCoverArt(self, imageWidget, songPath):
    fullSongPath = self.mpd.musicDirectory + "/" + songPath
    searchDirectory = re.findall("([^\n]+)/.+$", fullSongPath)[0]
    validExtensions = ["jpg", "jpeg", "png"]
    for ext in validExtensions:
      if sysPath.exists(searchDirectory + "/cover." + ext):
        self.setCoverArt(self.coverArt, searchDirectory + "/cover." + ext)
        break


  def findAndSetLyrics(self, lyricsLabel, songPath):
    # songPath does not include the music directory.
    songFileName = re.findall(r"(.*)\..+", (songPath.split("/"))[-1])[0]
    fullSongPath = self.mpd.musicDirectory + "/" + songPath
    searchDirectory = re.findall("(.*)/.*", fullSongPath)[0]
    if sysPath.exists(searchDirectory + "/lyrics/" + songFileName):
      f = open(searchDirectory + "/lyrics/" + songFileName)
      lyrics = f.read()
      f.close()
      if lyrics == "":
        lyricsLabel.set_label("Lyrics file is empty.")
      else:
        lyricsLabel.set_label(lyrics)
    else:
      lyricsLabel.set_label("No lyrics available.")


  def genreFilterChanged(self, box):
    if box.get_active() > 0:
      genre = box.get_active_text()
    else:
      genre = "NONE_SELECTED"
    self.libraryTreeView.set_cursor(Gtk.TreePath.new_from_indices([-1]))
    self.libraryTreeStore.clear()
    summary = self.populateLibrary(self.libraryTreeStore, self.libraryTreeView, genre)
    self.setLibraryInfoText(summary)

  
  def getNowPlusSeconds(self, seconds):
    return time.localtime(time.time() + seconds)


  def getPlaylistDurations(self):
    status = self.mpd.send("status")
    currentSongPos = re.findall("[\n]?song: ([0-9]+)", status)
    if len(currentSongPos) > 0:
      currentSongPos = int(currentSongPos[0])
    else:
      currentSongPos = 0
    elapsedTime_currentSong = re.findall("[\n]?time: ([0-9]+)", status)
    if len(elapsedTime_currentSong) > 0:
      elapsedTime_currentSong = int(elapsedTime_currentSong[0])
    else:
      elapsedTime_currentSong = 0
    trackDurations = re.findall("[\n]?Time: ([0-9]+)", self.mpd.send("playlistinfo"))
    totalPlaylistDuration = 0
    remainingPlaylistDuration = 0
    for i in range(0, len(trackDurations)):
      totalPlaylistDuration += int(trackDurations[i])
      if i == currentSongPos:
        remainingPlaylistDuration += int(trackDurations[i]) - int(elapsedTime_currentSong)
      if i > currentSongPos:
        remainingPlaylistDuration += int(trackDurations[i])

    return {"total": totalPlaylistDuration, "remaining": remainingPlaylistDuration}


  def libraryEntryClicked(self, selection):
    self.setCoverArt(self.coverArt, sysPath.join(BASEDIR, "noCover.png"))

    model, paths = selection.get_selected_rows() # The index list of the selected entries.
    
    # When searching the library treeview by typing, the paths list is empty, so this condition has to be handled.
    if len(paths) > 0:
      latestListEntry = model.get_iter(paths[-1]) # The cover to be displayed is the one for the last album in the list of selections.

      # The entries that are used to search the database.
      artist = model.get_value(latestListEntry, 0)
      album = model.get_value(latestListEntry, 1)
      year = model.get_value(latestListEntry, 2)

      selectedAlbumInfo = self.mpd.send("find artist \"" + artist + "\" album \"" + album + "\" date \"" + year + "\"")

      tracklist_originDirectory = re.findall("file: ([^\n]+)", selectedAlbumInfo)[0]
      tracks = re.findall(r"file: .*?(?=file:|$)", selectedAlbumInfo, re.DOTALL)

      tracklist_tracks = re.findall("Track: ([^\n]+)", selectedAlbumInfo)
      if len(tracklist_tracks) > 0:
        tracklist_tracks_maxChars = max([len(str(int(t))) for t in tracklist_tracks])
      else:
        tracklist_tracks_maxChars = 1
      
      tracklist_genres = re.findall("Genre: ([^\n]+)", selectedAlbumInfo)
      if len(tracklist_genres) > 0:
        # Remove the duplicates from the list, …
        tracklist_genres = [*set(tracklist_genres)]
        # … sort them alphebetically, …
        tracklist_genres.sort()
        # … and join all entries.
        tracklist_genres = ", ".join(tracklist_genres)
      else:
        tracklist_genres = ""
      
      self.albumInfo_heading.set_markup("<span font=\"" + str(1.5 * self.defaultFontSize) + "\"><b>" + (album.replace("&","&amp;") if album != "" else "[unknown album]") + "</b></span> — " + (year if year != "" else "[unknown release date]"))
      self.albumInfo_subtitle.set_markup("by " + (artist.replace("&","&amp;") if artist != "" else "[unknown artist]") + "\n" + tracklist_genres)

      # Clear the tracklist grid.
      while len(self.albumInfo_tracklistGrid.get_children()) != 0:
        self.albumInfo_tracklistGrid.remove_column(0)

      # A variable that is supposed to keep track of inserted blank lines.
      # Blank lines occur in multi-disc album tracklists between the individual disc tracklists.
      blankLineOffset = 0
      trackDisc = None
      totalPlaytime = 0
      for i, t in enumerate(tracks):
        trackArtist = re.findall(r"^Artist: (.+)", t, re.MULTILINE)
        trackDisc_tmp = re.findall(r"^Disc: (.+)", t, re.MULTILINE)

        if not trackDisc and trackDisc_tmp:
          trackDisc = trackDisc_tmp[0]

        if trackDisc and trackDisc_tmp and trackDisc != trackDisc_tmp[0]:
          self.albumInfo_tracklistGrid.attach(Gtk.Label(), 0, i + blankLineOffset, 1, 1)
          self.albumInfo_tracklistGrid.attach(Gtk.Label(), 1, i + blankLineOffset, 1, 1)
          self.albumInfo_tracklistGrid.attach(Gtk.Label(), 2, i + blankLineOffset, 1, 1)
          blankLineOffset += 1
          trackDisc = trackDisc_tmp[0]

        trackNumber = re.findall(r"^Track: (.+)", t, re.MULTILINE)
        if len(trackNumber) > 0:
          trackNumber = trackNumber[0]
        else:
          trackNumber = "0"

        trackTitle = re.findall(r"^Title: (.+)", t, re.MULTILINE)
        if len(trackTitle) > 0:
          trackTitle = trackTitle[0]
        else:
          trackTitle = "[unknown track title]"

        # Getting the first element of the re.findall() result is save for each track has a length.
        trackDuration = re.findall(r"^Time: (.+)", t, re.MULTILINE)[0]

        self.albumInfo_tracklistGrid.attach(Gtk.Label(label = trackNumber, xalign = 1, yalign = 0, width_chars = tracklist_tracks_maxChars), 0, i + blankLineOffset, 1, 1)
        label = Gtk.Label()
        label.set_width_chars(30)
        label.set_max_width_chars(30)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(0)
        label.set_xalign(0)

        additionalArtistsString = ""
        if len(trackArtist) > 1:
          additionalArtistsString = "[feat. "
          for artistIndex in range(1, len(trackArtist)):
            additionalArtistsString += trackArtist[artistIndex]
            if artistIndex < len(trackArtist) - 2:
              additionalArtistsString += ", "
            if artistIndex == len(trackArtist) - 2:
              if len(trackArtist) > 3:
                additionalArtistsString += ", and "
              else:
                additionalArtistsString += " and "
          additionalArtistsString += "]"

        trackTitle += " " + additionalArtistsString
      
        label.set_label(trackTitle) # Replacing with a non-breaking space.
        
        self.albumInfo_tracklistGrid.attach(label, 1, i + blankLineOffset, 1, 1)
        self.albumInfo_tracklistGrid.attach(Gtk.Label(label = secondsToTime(int(trackDuration)), xalign = 1, yalign = 0, width_chars=8), 2, i + blankLineOffset, 1, 1)
        totalPlaytime = totalPlaytime + int(trackDuration)

      self.albumInfo_tracklistGrid.attach(Gtk.Label(), 1, len(tracks) + blankLineOffset, 1, 1)
      self.albumInfo_tracklistGrid.attach(Gtk.Label(label = "Total playtime:", xalign = 1), 1, len(tracks) + blankLineOffset + 1, 1, 1)
      self.albumInfo_tracklistGrid.attach(Gtk.Label(label = secondsToTime(totalPlaytime), xalign = 1), 2, len(tracks) + blankLineOffset + 1, 1, 1)

      self.albumInfo_tracklistGrid.show_all()

      # Reset scrolled window to the start/top (14).
      self.infoScroll.do_scroll_child(self.infoScroll, 14, False)

      self.findAndSetCoverArt(self.coverArt, tracklist_originDirectory)


  def notebookPageSwitched(self, notebook, pageContents, pageIndex):
    tabLabel = notebook.get_tab_label_text(notebook.get_nth_page(pageIndex))
    #print(tabLabel)
    if tabLabel == "Library":
      self.libraryEntryClicked(self.libraryTreeView.get_selection())
      for child in self.infoScroll.get_children():
        self.infoScroll.remove(child)      
      self.infoScroll.add(self.albumInfoBox)
      self.editLyricsButton.set_visible(False)
      self.editTagsButton.set_visible(True)
      #self.libraryTreeView.show()
      self.libraryTreeView.grab_focus() # Does not work and focuses the filter dropdown menu instead. Why?
      
    elif tabLabel == "Playlist":
      status = self.mpd.send("status")
      currentSongPos = re.findall("[\n]?song: ([^\n]+)", status)
      if len(currentSongPos) > 0:
        currentSongPos = currentSongPos[0]
      else:
        currentSongPos = "0"

      currentSongInfo = self.mpd.send("playlistinfo " + currentSongPos)
      print(currentSongInfo)
      # Only proceed if the playlist is not empty.
      if len(currentSongInfo) > 0:
        songDirectory = re.findall("file: ([^\n]+)", currentSongInfo)[0]
        self.findAndSetCoverArt(self.coverArt, songDirectory)
        
        currentSong_title = (re.findall("Title: ([^\n]+)", currentSongInfo)[0]) # Replacing with a non-breaking space.
        currentSong_album = re.findall("Album: ([^\n]+)", currentSongInfo)[0]
        currentSong_artist = re.findall("Artist: ([^\n]+)", currentSongInfo)[0]
        self.currentSongInfo_heading.set_markup("<span font=\"" + str(1.5 * self.defaultFontSize) + "\"><b>" + currentSong_title.replace("&","&amp;").replace("feat. ", "feat. ") + "</b></span>")
        self.currentSongInfo_subtitle.set_markup("from »" + currentSong_album.replace("&","&amp;") + "« by " + currentSong_artist.replace("&","&amp;"))

        self.findAndSetLyrics(self.currentSongInfo_lyrics, songDirectory)
        
        for child in self.infoScroll.get_children():
          self.infoScroll.remove(child)
        self.infoScroll.add(self.currentSongInfoBox)
        self.editTagsButton.set_visible(False)
        self.editLyricsButton.set_visible(True)


  def openLyricsEditor(self, button):
    self.editLyricsButton.handler_block(self.editLyricsButton_connectID)
    window = lyricsEditor(self)
    

  def openTagEditor(self, button):
    print("To do! Open tags editor.")


  def playlistEntryDoubleclicked(self, treeview, path, column):
    self.mpd.send("play " + str(path.get_indices()[0]))


  def populateGenreFilter(self):
    genreList = self.mpd.send("list genre").split("\n")
    self.genreFilterBox.insert_text(0, "no filter")
    self.genreFilterBox.set_active(0)
    for genre in genreList:
      genre = re.sub("^Genre: ", "", genre)
      self.genreFilterBox.append(None, genre)


  def populateLibrary(self, treestore, treeview, genre = "NONE_SELECTED", prevSelectedEntry = []):
    prevSelectedIndex = 0
    newEntriesCount = 0
    model = treeview.get_model()
    print("Populating library with gerne " + genre)
    if genre != "NONE_SELECTED":
      albumLines = self.mpd.send("list album genre \"" + genre + "\" group date group artist group artistsort").split("\n")
    else:
      albumLines = self.mpd.send("list album group date group artist group artistsort").split("\n")
    albumsCount = 0
    listEntry = []
    currentArtist = ""
    currentArtistSort = ""
    currentDate = ""
    currentAlbum = ""

    print("SEARCHING IN ", albumLines)

    if len(albumLines) > 0:
      for i in range(0, len(albumLines)):
        #if re.match("^ArtistSort: ", albumLines[i]):
        #  currentArtistSort = re.sub("^ArtistSort: ", "", albumLines[i])
        if re.match("^Artist: ", albumLines[i]):
          currentArtist = re.sub("^Artist: ", "", albumLines[i])
        if re.match("^Date: ", albumLines[i]):
          currentDate = re.sub("^Date: ", "", albumLines[i])
        if re.match("^Album: ", albumLines[i]):
          if currentAlbum == re.sub("^Album: ", "", albumLines[i]):
            # Duplicate album names for the same artist appear, if at least one track has at least one additional (guest) artist.
            continue
          else:
            currentAlbum = re.sub("^Album: ", "", albumLines[i])
            listEntry = [currentArtist, currentAlbum, currentDate]
            # Overwrite entries if they already exist in the treestore …
            if len(treestore) > newEntriesCount:
              path = Gtk.TreePath.new_from_indices([newEntriesCount])
              iterator = model.get_iter(path)
              treestore.set(iterator, [0, 1, 2], listEntry)
            # … and append them if the treestore is not long enough already.
            # This procedure reduces the amount of times the treestore length has to change while populating the library.
            else:
              treestore.append(listEntry)
            
            newEntriesCount += 1
            
            # Used when re-populating the library after having updated the database.
            # Try to restore the previous selection by row values.
            if len(prevSelectedEntry) == 3 and "".join(listEntry) == "".join(prevSelectedEntry):
              prevSelectedIndex = newEntriesCount - 1
            # Only count actual albums and ignore empty album tags.
            if currentAlbum != "":
              albumsCount += 1
      
      treeview.set_cursor(Gtk.TreePath.new_from_indices([prevSelectedIndex]))

    # Delete the excess library entries.
    # This is needed after updating the database and re-populating the library, because the amount of albums listed might have decreased.
    while len(treestore) > newEntriesCount:
      iterator = model.get_iter(Gtk.TreePath.new_from_indices([len(treestore) - 1]))
      treestore.remove(iterator)

    stats = self.mpd.send("stats")
    artistsCount = re.findall("\nartists: ([0-9]+)\n", stats)[0]
    songsCount = re.findall("\nsongs: ([0-9]+)\n", stats)[0]
    return artistsCount + " artists, " + str(albumsCount) + " albums, " + songsCount + " songs"
    

  def populatePlaylist(self, treestore, treeview):
    activeSong = self.mpd.send("currentsong")
    activeSongPos = re.findall("\nPos: ([^\n]+)", activeSong)
    if len(activeSongPos) > 0:
      activeSongPos = activeSongPos[0]
    else:
      activeSongPos = 0

    playlist = self.mpd.send("playlistinfo").split("\n")
    listEntry = []
    currentTrack = ""
    currentTitle = ""
    for i in range(0, len(playlist)):
      if re.match("^Track: ", playlist[i]):
        currentTrack = re.sub("^Track: ", "", playlist[i])
      if re.match("^Title: ", playlist[i]):
        currentTitle = re.sub("^Title: ", "", playlist[i]).replace("&", "&amp;")
      if re.match("^Time: ", playlist[i]):
        convertedDuration = secondsToTime(int(re.sub("^Time: ", "", playlist[i])))
        listEntry = [currentTrack, currentTitle, convertedDuration]
        treestore.append(listEntry)
        if len(self.playlistTreeStore) - 1 == int(activeSongPos):
          self.setTreeviewRowBold(treeview, int(activeSongPos))
        listEntry = []


  def setCoverArt(self, imageWidget, path):
    pixbuf = Pixbuf.new_from_file_at_scale(path, 28 * self.defaultFontSize, 28 * self.defaultFontSize, True)
    imageWidget.set_from_pixbuf(pixbuf)

    imageWidget.set_margin_start( int((28 * self.defaultFontSize - pixbuf.get_width()) / 2) + 0.5 * self.defaultFontSize)
    imageWidget.set_margin_end( 29 * self.defaultFontSize - imageWidget.get_margin_start() - pixbuf.get_width()) 
    imageWidget.set_margin_top( int((28 * self.defaultFontSize - pixbuf.get_height()) / 2) + 0.5 * self.defaultFontSize)
    imageWidget.set_margin_bottom( 29 * self.defaultFontSize - imageWidget.get_margin_top() - pixbuf.get_height()) 


  def setLibraryInfoText(self, text):
    self.libraryInfo.set_label(text)


  def setTreeviewRowBold(self, treeview, rowNumber):
    # This routine needs a fix! The GUI gets fragile and is prone to crashing.
    model = treeview.get_model()
    path = Gtk.TreePath.new_from_indices([rowNumber])
    iterator = model.get_iter(path)
    row = treeview.get_columns()
    for i in range(0, len(row)):
      row[i] = "<b>" + model.get_value(iterator, i) + "</b>"
    model.set_row(iterator, row)


  def setTreeviewRowLight(self, treeview, rowNumber):
    model = treeview.get_model()
    path = Gtk.TreePath.new_from_indices([rowNumber])
    iterator = model.get_iter(path)
    row = treeview.get_columns()
    for i in range(0, len(row)):
      row[i] = re.sub("</?b>", "", model.get_value(iterator, i))
    model.set_row(iterator, row)


  def songChanged(self):
    result = self.idleThread_player.poll()
    if result == None:
      # The process has not finished yet, i. e. the song has not changed.
      # Ask again in 100 ms.
      GLib.timeout_add(100, self.songChanged)
    else:
      self.updateGUIForChangedSong()

  
  def songProgressClicked(self, box, event):
    status = self.mpd.send("status")
    state = re.findall("[\n]?state: ([^\n]+)", status)[0]
    if state == "play" or state == "pause":    
      skipToPosition = int(event.x)
      progressBarWidth = int(self.songProgress.get_allocated_width())
      totalSongLength = int(re.findall("[\n]?time: [0-9]+:([0-9]+)", status)[0])
      
      self.songProgress.set_fraction(skipToPosition / progressBarWidth)
      self.songProgress.set_text(secondsToTime(int(skipToPosition / progressBarWidth * totalSongLength)) + "/" + secondsToTime(totalSongLength))

      self.mpd.send("seekcur " + str(int( skipToPosition / progressBarWidth * totalSongLength)))
      # To do: Update playlist end time.


  def updateGUIForChangedSong(self):
    currentSong = self.mpd.send("currentsong")
    
    # currentSong may be empty when the playlist is replaced.
    # The player then stops and tries to update the GUI, but fails, as there is no current song.
    # Use information from the new playlist instead.
    if len(currentSong) == 0:
      currentSong = self.mpd.send("playlistinfo")

    # The following condition is not met when the user deletes the last song of a playlist which is also currently playing.
    if len(currentSong) > 0:
      artist = re.findall("Artist: ([^\n]+)", currentSong)[0]
      title = re.findall("Title: ([^\n]+)", currentSong)[0]
      self.set_title("»" + title + "« by " + artist)

      album = re.findall("Album: ([^\n]+)", currentSong)[0]
      self.currentSongInfo_heading.set_markup("<span font=\"" + str(1.5 * self.defaultFontSize) + "\"><b>" + title.replace("&","&amp;") + "</b></span>")
      self.currentSongInfo_subtitle.set_markup("from »" + album.replace("&","&amp;") + "« by " + artist.replace("&","&amp;"))

      tabLabel = self.notebook.get_tab_label_text(self.notebook.get_nth_page(self.notebook.get_current_page()))
      if tabLabel == "Playlist":
        # Reset scrolled window to the start/top (14).
        self.infoScroll.do_scroll_child(self.infoScroll, 14, False)

      songDirectory = re.findall("file: ([^\n]+)", currentSong)[0]
      self.findAndSetLyrics(self.currentSongInfo_lyrics, songDirectory)
      if self.notebook.get_tab_label_text(self.notebook.get_nth_page(self.notebook.get_current_page())) == "Playlist":
        self.findAndSetCoverArt(self.coverArt, songDirectory)
  
      self.updateSongProgress()
      
      self.setTreeviewRowLight(self.playlistTreeView, self.currentSongPos)
      
      # Set the new currentSongPos value.
      self.currentSongPos = int(re.findall("[\n]?Pos: ([^\n]+)", currentSong)[0])
  
      self.setTreeviewRowBold(self.playlistTreeView, self.currentSongPos)
  
      state = re.findall("[\n]state: ([^\n]+)", self.mpd.send("status"))[0]
      if state == "stop" or state == "pause":
        self.button_pause_play.set_image(Gtk.Image.new_from_icon_name("media-playback-start", 4))
      # updateGUIForChangedSong can also be triggered by double-clicking a playlist entry when the player is stopped.
      # In this case, change the pause-play-button image to the pause icon.
      else:
        self.button_pause_play.set_image(Gtk.Image.new_from_icon_name("media-playback-pause", 4))
        # Workaround for an MPD bug.
        status = self.mpd.send("status")
        currentPlaybackPosition = re.findall("[\n]?elapsed: ([^\n]+)", status)[0]
        self.mpd.send("pause")
        # Skip back by one second to prevent the »pause« command from skipping playback time, especially the very first second of a song.
        self.mpd.send("seekcur " + str(max(0, int(float(currentPlaybackPosition)) - 1)))
        self.mpd.send("play")

      self.updatePlaylistPlaytimeInfo()
  
      self.idleThread_player = subprocess.Popen(["python", sys.argv[0], "idle player"], 0)
      self.songChanged()
    else:
      self.button_pause_play.set_image(Gtk.Image.new_from_icon_name("media-playback-start", 4))


  def updatePlaylistPlaytimeInfo(self):
    playlistDurations = self.getPlaylistDurations()
    playlistEndTime = self.getNowPlusSeconds(playlistDurations['remaining'])
    playlistEndTime_hour = str(playlistEndTime.tm_hour) if playlistEndTime.tm_hour > 9 else "0" + str(playlistEndTime.tm_hour)
    playlistEndTime_min = str(playlistEndTime.tm_min) if playlistEndTime.tm_min > 9 else "0" + str(playlistEndTime.tm_min)
    self.playlistPlaytimeInfo.set_label("total: " + str(secondsToTime(playlistDurations['total'])) + "; ends at " + playlistEndTime_hour + ":" + playlistEndTime_min)


  def updatePlaylistPlaytimeInfo_bgLoop(self):
    GLib.timeout_add(1000, self.updatePlaylistPlaytimeInfo_renewLoop)


  def updatePlaylistPlaytimeInfo_renewLoop(self):
    self.updatePlaylistPlaytimeInfo()
    self.updatePlaylistPlaytimeInfo_bgLoop()


  def updateSongProgress(self):
    status = self.mpd.send("status")
    state = re.findall("[\n]?state: ([^\n]+)", status)[0]
    if state == "play" or state == "pause":
      currentSongLength = re.findall("[\n]?time: ([0-9]+):[0-9]+", status)[0]
      totalSongLength = re.findall("[\n]?time: [0-9]+:([0-9]+)", status)[0]
      self.songProgress.set_fraction(int(currentSongLength) / int(totalSongLength))
      self.songProgress.set_text(secondsToTime(int(currentSongLength)) + "/" + secondsToTime(int(totalSongLength)))
      if state == "play":
        GLib.timeout_add(1000, self.updateSongProgress)
    elif state == "stop":
      currentSong = self.mpd.send("playlistinfo 0")
        # Avoid querying empty playlists.
      if len(currentSong) > 0:
        tmpList = self.mpd.send("currentsong")
        if len(tmpList) > 0:
          currentSong = tmpList
        totalSongLength = re.findall("[\n]?Time: ([0-9]+)\n", currentSong)[0]
        self.songProgress.set_fraction(0)
        self.songProgress.set_text(secondsToTime(0) + "/" + secondsToTime(int(totalSongLength)))
      else:
        self.songProgress.set_text("00:00/00:00")
        self.songProgress.set_fraction(0)
        self.set_title("Playlist is empty")


  def volumeChanged(self, scale, jump, newValue):
    self.mpd.send("setvol " + str(int(newValue)))


  def quit(self, gui):
    self.mpd.connection.close()
    Gtk.main_quit()


if len(sys.argv) > 1:
  client = mpdClient()
  answer = client.send(" ".join(sys.argv[1:]))
  print(answer)
  client.connection.close()
else:
  #guiAlreadyRunning = True if sysExec("ps -x | grep mpd_gui.py$") == 0 else False
  #if not guiAlreadyRunning:
    mpdGUI()
  #else:
  #  sysExec('notify-send "MPD Notification" "GUI is already running."')
