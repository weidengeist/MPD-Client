# -*- coding: utf-8 -*-
# line above is necessary for symbols », «, and more

# General functionality modules.
from os import path as sysPath
from os import listdir
#from os import mkdir
import re
#import socket
#import subprocess
import sys # Enables using command line arguments.
#import time

# GTK GUI.
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
#from gi.repository import Gdk

# MP3 handling.
from mutagen.mp3 import MP3
import mutagen.id3

from gi.repository import GLib # For GLib.timeout_add.
from gi.repository import Gio

import gi.repository.GdkPixbuf as GdkPixbuf
from gi.repository.GdkPixbuf import Pixbuf
#from gi.repository import Pango

import io
import copy # Enables deepcopy command to copy arrays and classes.

from PIL import Image

# Get the base directory. This is needed for evaluating symbolic links to the original program path.
BASEDIR = sysPath.join("/".join(sysPath.realpath(sys.argv[0]).split("/")[0:-1]))

# A list of id3 tags of loaded files to keep track of changes.
TAGDATA = { 'current' : [], 'new' : []}

# This list can be retrieved from https://id3.org/id3v2.4.0-frames.
frameList = [
  ["AENC", "Audio encryption"],
  #["APIC", "Attached picture"],
  ["ASPI", "Audio seek point index"],
  #["COMM", "Comments"], # Separate input.
  ["COMR", "Commercial frame"],
  ["ENCR", "Encryption method registration"],
  ["EQU2", "Equalisation 2"],
  ["ETCO", "Event timing codes"],
  ["GEOB", "General encapsulated object"],
  ["GRID", "Group identification registration"],
  ["LINK", "Linked information"],
  ["MCDI", "Music CD identifier"],
  ["MLLT", "MPEG location lookup table"],
  ["OWNE", "Ownership frame"],
  ["PCNT", "Play counter"],
  ["POPM", "Popularimeter"],
  ["POSS", "Position synchronisation frame"],
  #["PRIV", "Private frame"], # Needs further investigation on how this tag is built.
  ["RBUF", "Recommended buffer size"],
  ["RVA2", "Relative volume adjustment 2"],
  ["RVRB", "Reverb"],
  ["SEEK", "Seek frame"],
  ["SIGN", "Signature frame"],
  #["SYLT", "Synchronised lyric/text"], # Implement this separately.
  ["SYTC", "Synchronised tempo codes"],
  #"TALB", "Album/Movie/Show title"],
  ["TBPM", "BPM", "beats per minute)"],
  ["TCOM", "Composer"],
  #"TCON", "Content type"], Genre
  ["TCOP", "Copyright message"],
  ["TDEN", "Encoding time"],
  ["TDLY", "Playlist delay"],
  ["TDOR", "Original release time"],
  ["TDRC", "Recording time"],
  #["TDRL", "Release time"],################ Check here. MPD support TDRC vs. TDRL.
  ["TDTG", "Tagging time"],
  ["TENC", "Encoded by"],
  ["TEXT", "Lyricist/Text writer"],
  ["TFLT", "File type"],
  ["TIPL", "Involved people list"],
  ["TIT1", "Content group description"],
  #"TIT2", "Title/songname/content description"],
  ["TIT3", "Subtitle/Description refinement"],
  ["TKEY", "Initial key"],
  ["TLAN", "Language(s)"],
  ["TLEN", "Length"],
  ["TMCL", "Musician credits list"],
  ["TMED", "Media type"],
  ["TMOO", "Mood"],
  ["TOAL", "Original album/movie/show title"],
  ["TOFN", "Original filename"],
  ["TOLY", "Original lyricist(s)/text writer(s)"],
  ["TOPE", "Original artist(s)/performer(s)"],
  ["TOWN", "File owner/licensee"],
  #"TPE1", "Lead performer(s)/Soloist(s)"],
  ["TPE2", "Band/orchestra/accompaniment"],
  ["TPE3", "Conductor/performer refinement"],
  ["TPE4", "Interpreted, remixed, or otherwise modified by"],
  #"TPOS", "Part of a set"], # Disc number.
  ["TPRO", "Produced notice"],
  ["TPUB", "Publisher"],
  #"TRCK", "Track number/Position in set"],
  ["TRSN", "Internet radio station name"],
  ["TRSO", "Internet radio station owner"],
  ["TSOA", "Album sort order"],
  ["TSOP", "Performer sort order"],
  ["TSOT", "Title sort order"],
  ["TSRC", "international standard recording code (ISRC)"],
  ["TSSE", "Software/Hardware and settings used for encoding"],
  ["TSST", "Set subtitle"],
  #["TXXX", "User defined text information frame"], # Separate input area.
  ["UFID", "Unique file identifier"],
  ["USER", "Terms of use"],
  #["USLT", "Unsynchronised lyric/text transcription"], # Using a separate text area for this.
  ["WCOM", "Commercial information"],
  ["WCOP", "Copyright/Legal information"],
  ["WOAF", "Official audio file webpage"],
  ["WOAR", "Official artist/performer webpage"],
  ["WOAS", "Official audio source webpage"],
  ["WORS", "Official Internet radio station homepage"],
  ["WPAY", "Payment"],
  ["WPUB", "Publishers official webpage"],
  #["WXXX", "User defined URL link frame"] # Separate input area.
]

# The list of general frames excluded from the list above.
generalTagsList = [["Artist", "TPE1"], ["Title", "TIT2"], ["Album", "TALB"], ["Date", "TDRL"], ["Genre", "TCON"]]


class tagEditor(Gtk.Window):
  def __init__(self, parent, songs = []):
    super().__init__()

    # Get the system default font size. Needed for varying font sizes in info panels.
    f = open(sysPath.expanduser("~") + "/.config/gtk-3.0/settings.ini", "r")
    self.defaultFontSize = int(re.findall("gtk-font-name=.*?([0-9]+)\n", f.read())[0])
    f.close()
    
    self.set_default_icon_name("id3v2-editor")
    self.set_title("WeiD3 — ID3v2 tag editor")
    self.set_default_size(1, 1)
    self.set_transient_for(parent)
    self.set_position(4)
    #self.connect("destroy", self.quit, parent)

    # The box containing the main vbox elements.
    hbox_main = Gtk.HPaned()
    hbox_main.set_margin_top(0.5 * self.defaultFontSize)
    hbox_main.set_margin_bottom(0.5 * self.defaultFontSize)
    hbox_main.set_margin_start(0.5 * self.defaultFontSize)
    hbox_main.set_margin_end(0.5 * self.defaultFontSize)
  
    # The box containing the file list and file rename frame.
    vbox_fileListAndRename = Gtk.VBox(spacing = 0.5 * self.defaultFontSize)


    ############################################################################
    # A button for adding files if no files have been passed via command line. #
    ############################################################################

    fileChooser = Gtk.ToolButton()
    fileChooser.set_icon_name('document-open')
    fileChooser.set_tooltip_text("Choose files …")
    
    fileChooser.connect("clicked", self.addFilesToFileList)

    hbox_chooserButton = Gtk.HBox()
    hbox_chooserButton.pack_start(fileChooser, False, False, 0)
    hbox_chooserButton.pack_start(Gtk.HBox(), True, True, 0)

    vbox_fileListAndRename.pack_start(hbox_chooserButton, False, False, 0)
    

    ############################
    # Composing the file list. #
    ############################

    # List store contains the full file path ([0]) and the file name ([1]).
    self.fileListStore = Gtk.ListStore(str, str)
    self.fileListTreeview = Gtk.TreeView(model = self.fileListStore)
    self.fileListTreeview.props.reorderable = True
    self.fileListTreeview.get_selection().connect("changed", self.selectedFileChanged)

    renderer = Gtk.CellRendererText()
    renderer.set_alignment(0, 0)
    column = Gtk.TreeViewColumn("Files", cell_renderer = renderer, text = 1)
    column.set_resizable(True)
    self.fileListTreeview.append_column(column)

    scroller = Gtk.ScrolledWindow()
    scroller.add(self.fileListTreeview)

    vbox_fileListAndRename.pack_start(scroller, True, True, 0)


    ######################################
    # Composing the file rename section. #
    ######################################

    frame_fileRename = Gtk.Frame(label = "Rename file(s) by tags")

    vbox_fileRenameWidgets = Gtk.VBox(spacing = 2)

    self.trackIncludesTotalCheckbox = Gtk.CheckButton(label = "[%Track] includes total track number")
    vbox_fileRenameWidgets.pack_start(self.trackIncludesTotalCheckbox, False, False, 0)

    self.discIncludesTotalCheckbox = Gtk.CheckButton(label = "[%Disc] includes total track number")
    vbox_fileRenameWidgets.pack_start(self.discIncludesTotalCheckbox, False, False, 0)

    self.trackNumberDigits = Gtk.SpinButton.new_with_range(1, 3, 1)
    self.trackNumberDigits.set_width_chars(2)
    hbox = Gtk.HBox(spacing = 5)
    hbox.pack_start(self.trackNumberDigits, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Minimum digits in track number"), False, False, 0)
    vbox_fileRenameWidgets.pack_start(hbox, False, False, 0)

    self.discNumberDigits = Gtk.SpinButton.new_with_range(1, 3, 1)
    self.discNumberDigits.set_width_chars(2)
    hbox = Gtk.HBox(spacing = 5)
    hbox.pack_start(self.discNumberDigits, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Minimum digits in disc number"), False, False, 0)
    vbox_fileRenameWidgets.pack_start(hbox, False, False, 0)

    vbox_fileRenameWidgets.pack_start(Gtk.HSeparator(margin_bottom = 0.5 * self.defaultFontSize, margin_top = 0.5 * self.defaultFontSize), False, False, 0)

    self.fileNamePattern = Gtk.Entry(hexpand = True, width_chars = 32)
    self.fileNamePattern.set_sensitive(False)
    self.fileNamePattern.set_placeholder_text("Hover to get further information.")
    self.fileNamePattern.set_tooltip_text("Use [%Artist], [%Title], etc. from the general tags or any ID3 frame (e.g. [%TIT2]) to use track information for the file name.")
    self.fileNamePattern.connect("changed", self.updateFileNamePreview)
    self.fileNamePreview = Gtk.Label(label = "No pattern to evaluate.", width_chars = 48, xalign = 0)
    grid = Gtk.Grid(column_spacing = 5, row_spacing = 0.5 * self.defaultFontSize)
    grid.attach(Gtk.Label(label = "File name pattern:", xalign = 0), 0, 0, 1, 1)
    grid.attach(self.fileNamePattern, 1, 0, 1, 1)
    grid.attach(Gtk.Label(label = "File name preview:", xalign = 0), 0, 1, 1, 1)
    grid.attach(self.fileNamePreview, 1, 1, 1, 1)
    vbox_fileRenameWidgets.pack_start(grid, False, False, 0)

    hbox_renameButtons = Gtk.HBox(homogeneous = True, spacing = 5, margin_top = 0.5 * self.defaultFontSize)

    self.renameSelectedFileButton = Gtk.Button(label = "Rename selected file")
    self.renameSelectedFileButton.set_sensitive(False)
    self.renameSelectedFileButton.connect("clicked", self.renameSelectedFile)
    
    self.renameAllFilesButton = Gtk.Button(label = "Rename all files")
    self.renameAllFilesButton.set_sensitive(False)
    self.renameAllFilesButton.connect("clicked", self.renameAllFiles)

    self.hbox_renameWarning = Gtk.HBox(spacing = 5)
    self.hbox_renameWarning.props.opacity = 0.0
    warningIcon = Gtk.Image.new_from_icon_name("gtk-dialog-warning", 4)
    warningText = Gtk.Label(label = "Warning! Cannot rename files due to duplicate file names after rename.", xalign = 0)

    self.hbox_renameWarning.pack_start(warningIcon, False, False, 0)
    self.hbox_renameWarning.pack_start(warningText, True, True, 0)

    vbox_fileRenameWidgets.add(self.hbox_renameWarning)

    hbox_renameButtons.pack_start(self.renameSelectedFileButton, True, True, 0)
    hbox_renameButtons.pack_start(self.renameAllFilesButton, True, True, 0)
    
    vbox_fileRenameWidgets.pack_start(hbox_renameButtons, False, False, 0)

    frame_fileRename.add(vbox_fileRenameWidgets)

    vbox_fileListAndRename.pack_start(frame_fileRename, False, False, 0)

    # The box containing the two tagging frames.
    vbox_tags = Gtk.VBox(spacing = 0.5 * self.defaultFontSize)


    #########################################
    # Composing the frame for default tags. #
    #########################################

    self.tagsGrid_default = Gtk.Grid()
    self.tagsGrid_default.set_column_spacing(5)
    self.tagsGrid_default.set_row_spacing(0.5 * self.defaultFontSize)

    for i in range(len(generalTagsList)):
      # A button for copying the tag to other files.
      setattr(self, "tagCopyButton" + generalTagsList[i][1], Gtk.Button.new_from_icon_name("edit-copy", 4))
      getattr(self, "tagCopyButton" + generalTagsList[i][1]).set_sensitive(False)
      getattr(self, "tagCopyButton" + generalTagsList[i][1]).connect("clicked", self.copyTagValueToAllFiles, generalTagsList[i][1])
      getattr(self, "tagCopyButton" + generalTagsList[i][1]).set_tooltip_text("Copy " + generalTagsList[i][0].lower() + " to all other files.")
      self.tagsGrid_default.attach(getattr(self, "tagCopyButton" + generalTagsList[i][1]), 0, i, 1, 1)

      # A button for reverting the tag to its original value.
      setattr(self, "tagRevertButton" + generalTagsList[i][1], Gtk.Button.new_from_icon_name("edit-undo", 4))
      getattr(self, "tagRevertButton" + generalTagsList[i][1]).set_sensitive(False)
      getattr(self, "tagRevertButton" + generalTagsList[i][1]).connect("clicked", self.revertTag, generalTagsList[i][1])
      getattr(self, "tagRevertButton" + generalTagsList[i][1]).set_tooltip_text("Revert " + generalTagsList[i][0].lower() + " to its original value.")
      self.tagsGrid_default.attach(getattr(self, "tagRevertButton" + generalTagsList[i][1]), 8, i, 1, 1)

      tagLabel = Gtk.Label(label = generalTagsList[i][0], xalign = 0)
      tagLabel.set_tooltip_text(generalTagsList[i][1])
      self.tagsGrid_default.attach(tagLabel, 1, i, 1, 1)
      setattr(self, "tagEntry" + generalTagsList[i][1], Gtk.Entry(hexpand = True))
      getattr(self, "tagEntry" + generalTagsList[i][1]).set_sensitive(False)
      getattr(self, "tagEntry" + generalTagsList[i][1]).connect("changed", self.noteTagChange, generalTagsList[i][1])
      self.tagsGrid_default.attach(getattr(self, "tagEntry" + generalTagsList[i][1]), 2, i, 6, 1)

    self.tagsGrid_default.get_child_at(2, 4).set_tooltip_text("Multiple genres possible, separated by semicolon.")

    self.tagCopyButtonTRCK = Gtk.Button.new_from_icon_name("go-up", 4)
    self.tagCopyButtonTRCK.set_sensitive(False)
    self.tagCopyButtonTRCK.connect("clicked", self.enumerateOtherTracks)
    self.tagCopyButtonTRCK.set_tooltip_text("Enumerate following files with ascending track number.")
    self.tagsGrid_default.attach(getattr(self, "tagCopyButtonTRCK"), 0, 5, 1, 1)
    tagLabel = Gtk.Label(label = "Track", xalign = 0)
    tagLabel.set_tooltip_text("TRCK")
    self.tagsGrid_default.attach(tagLabel, 1, 5, 1, 1)

    self.tagEntryTRCK = Gtk.Entry(width_chars = 7, max_length = 7, hexpand = True)
    self.tagEntryTRCK.connect("changed", self.noteTagChange, "TRCK")
    self.tagEntryTRCK.set_sensitive(False)
    self.tagsGrid_default.attach(self.tagEntryTRCK, 2, 5, 1, 1)

    self.tagRevertButtonTRCK = Gtk.Button.new_from_icon_name("edit-undo", 4)
    self.tagRevertButtonTRCK.set_sensitive(False)
    self.tagRevertButtonTRCK.connect("clicked", self.revertTag, "TRCK")
    self.tagRevertButtonTRCK.set_tooltip_text("Revert track number to its original value.")
    self.tagsGrid_default.attach(self.tagRevertButtonTRCK, 3, 5, 1, 1)

    self.tagsGrid_default.attach(Gtk.Label(label = "|"), 4, 5, 1, 1)
    
    self.tagCopyButtonTPOS = Gtk.Button.new_from_icon_name("edit-copy", 4)
    self.tagCopyButtonTPOS.set_sensitive(False)
    self.tagCopyButtonTPOS.connect("clicked", self.copyTagValueToAllFiles)
    self.tagCopyButtonTPOS.set_tooltip_text("Copy disc number to all following files.")
    self.tagCopyButtonTPOS.set_hexpand(False)
    self.tagsGrid_default.attach(self.tagCopyButtonTPOS, 5, 5, 1, 1)
    
    tagLabel = Gtk.Label(label = "Disc", xalign = 1, margin_right = 5)
    tagLabel.set_tooltip_text("TPOS")
    self.tagsGrid_default.attach(tagLabel, 6, 5, 1, 1)
    self.tagEntryTPOS = Gtk.Entry(width_chars = 7, max_length = 7, hexpand = True)
    self.tagEntryTPOS.connect("changed", self.noteTagChange, "TPOS")
    self.tagEntryTPOS.set_sensitive(False)
    #buttonLabelBox.pack_start(tagEntry, False, False, 0)
    self.tagsGrid_default.attach(self.tagEntryTPOS, 7, 5, 1, 1)

    self.tagRevertButtonTPOS = Gtk.Button.new_from_icon_name("edit-undo", 4)
    self.tagRevertButtonTPOS.set_sensitive(False)
    self.tagRevertButtonTPOS.connect("clicked", self.revertTag, "TPOS")
    self.tagRevertButtonTPOS.set_tooltip_text("Revert disc number to its original value.")
    self.tagsGrid_default.attach(self.tagRevertButtonTPOS, 8, 5, 1, 1)

    hbox_coverLabelButtonButton = Gtk.HBox(spacing = 5, homogeneous = True)
    #hbox_coverLabelButtonButton.pack_start(Gtk.HBox(), True, True, 0)
    #hbox_coverLabelButtonButton.pack_start(Gtk.Label(label = "Cover art (APIC)"), False, False, 0)
    self.setCoverArtButton = Gtk.Button(label = "Set cover …")
    self.setCoverArtButton.set_sensitive(False)
    self.setCoverArtButton.connect("clicked", self.chooseCoverArt)
    hbox_coverLabelButtonButton.pack_start(self.setCoverArtButton, True, True, 0)

    self.clearCoverButton = Gtk.Button(label = "Clear cover art")
    self.clearCoverButton.set_sensitive(False)
    self.clearCoverButton.connect("clicked", self.clearCoverArt)
    hbox_coverLabelButtonButton.pack_start(self.clearCoverButton, True, True, 0)

    vbox_coverButtons = Gtk.VBox(spacing = 5)
    vbox_coverButtons.pack_start(hbox_coverLabelButtonButton, False, False, 0)

    self.copyCoverToAllFilesButton = Gtk.Button(label = "Copy cover to all other files", image = Gtk.Image.new_from_icon_name("edit-copy", 4))
    self.copyCoverToAllFilesButton.set_sensitive(False)
    self.copyCoverToAllFilesButton.connect("clicked", self.copyTagValueToAllFiles, "APIC")
    vbox_coverButtons.pack_start(self.copyCoverToAllFilesButton, True, True, 0)

    self.tagRevertButtonAPIC = Gtk.Button(label = "Revert this cover", image = Gtk.Image.new_from_icon_name("edit-undo", 4))
    self.tagRevertButtonAPIC.set_sensitive(False)
    self.tagRevertButtonAPIC.connect("clicked", self.revertTag, "APIC")

    self.tagRevertAllButtonAPIC = Gtk.Button(label = "Revert all covers", image = Gtk.Image.new_from_icon_name("edit-undo", 4))
    self.tagRevertAllButtonAPIC.set_sensitive(False)
    self.tagRevertAllButtonAPIC.connect("clicked", self.revertTagInEveryFile, "APIC")

    hbox_coverReversion = Gtk.HBox(spacing = 5, homogeneous = True)
    hbox_coverReversion.pack_start(self.tagRevertButtonAPIC, True, True, 0)
    hbox_coverReversion.pack_start(self.tagRevertAllButtonAPIC, True, True, 0)

    vbox_coverButtons.pack_start(hbox_coverReversion, True, True, 0)

    hbox_coverArt = Gtk.HBox()
    self.coverArt = Gtk.Image()
    self.coverFrame = Gtk.Frame()
    self.coverFrame.add(self.coverArt)
    self.coverFrame.connect("size-allocate", self.coverArtFrameChangedSize)
    #hbox_coverArt.pack_start(Gtk.HBox(), True, True, 0)
    hbox_coverArt.pack_start(self.coverFrame, True, True, 0)
    #hbox_coverArt.pack_start(Gtk.HBox(), True, True, 0)
    self.setCoverArt(sysPath.join(BASEDIR, "noCover.png"))

    vbox_coverAndButtons = Gtk.VBox(spacing = 5)
    vbox_coverAndButtons.pack_start(Gtk.Label(label = "Cover art (APIC)", xalign = 0), False, False, 0)
    vbox_coverAndButtons.pack_start(hbox_coverArt, True, True, 0)
    vbox_coverAndButtons.pack_start(vbox_coverButtons, True, True, 0)

    vbox_defaultTags = Gtk.VBox(spacing = 5)
    vbox_defaultTags.pack_start(Gtk.Label(label = "General tags", xalign = 0, margin_bottom = 0.5 * self.defaultFontSize), False, False, 0)
    vbox_defaultTags.pack_start(self.tagsGrid_default, False, False, 0)
    
    #hbox_coverAndDefaultTags = Gtk.HPaned()
    #hbox_coverAndDefaultTags.pack1(vbox_defaultTags, True, False)
    #hbox_coverAndDefaultTags.pack2(vbox_coverAndButtons, False, False)

    hbox_coverAndDefaultTags = Gtk.HBox(spacing = 5)
    hbox_coverAndDefaultTags.pack_start(vbox_defaultTags, True, True, 0)
    hbox_coverAndDefaultTags.pack_start(vbox_coverAndButtons, False, False, 0)
    

    ##################
    # Extended tags. #
    ##################

    self.addExtendedTagsButton = Gtk.Button(label = "Add new extended tag", image = Gtk.Image.new_from_icon_name("list-add", 4), hexpand = False, margin_bottom = 0.5 * self.defaultFontSize)
    self.addExtendedTagsButton.set_sensitive(False)
    self.addExtendedTagsButton_connectID = self.addExtendedTagsButton.connect("clicked", self.openExtendedTagsList)

    # The scroller and the grid with the tag entry lines.
    scroller_extendedTags = Gtk.ScrolledWindow()
    scroller_extendedTags.set_size_request(200, 16 * self.defaultFontSize)
    self.tagsGrid_extended = Gtk.Grid(margin = 0.5 * self.defaultFontSize)#, margin_bottom = 0.5 * self.defaultFontSize)
    self.tagsGrid_extended.set_column_spacing(5)
    self.tagsGrid_extended.set_row_spacing(0.5 * self.defaultFontSize)

    scroller_extendedTags.add(self.tagsGrid_extended)
    vbox_extendedTagsArea = Gtk.VBox()

    hbox_addExtendedTagsButton = Gtk.HBox()
    hbox_addExtendedTagsButton.pack_start(Gtk.Label(), True, True, 0)
    hbox_addExtendedTagsButton.pack_start(self.addExtendedTagsButton, False, False, 0)
    
    vbox_extendedTagsArea.pack_start(hbox_addExtendedTagsButton, False, False, 0)
    vbox_extendedTagsArea.pack_start(scroller_extendedTags, True, True, 0)
    
    expander_extendedTags = Gtk.Expander(label = "Extended tags")
    expander_extendedTags.set_resize_toplevel(True)
    #expander_extendedTags.connect("activate", self.expanderClicked)

    expander_extendedTags.add(vbox_extendedTagsArea)


    ####################
    # Custom comments. #
    ####################

    expander_customComments = Gtk.Expander(label = "Custom comments (COMM)")
    expander_customComments.set_resize_toplevel(True)

    # Button for adding new comments.
    self.addCommentButton = Gtk.Button(label = "Add new comment", image = Gtk.Image.new_from_icon_name("list-add", 4), hexpand = False, margin_bottom = 0.5 * self.defaultFontSize)
    self.addCommentButton.set_sensitive(False)
    self.addCommentButton.connect("clicked", self.addCommentLine)

    hbox_addCommentButton = Gtk.HBox()
    hbox_addCommentButton.pack_start(Gtk.Label(), True, True, 0)
    hbox_addCommentButton.pack_start(self.addCommentButton, False, False, 0)
    
    self.commentsGrid = Gtk.Grid(margin = 0.5 * self.defaultFontSize)#, margin_bottom = 0.5 * self.defaultFontSize)
    self.commentsGrid.set_column_spacing(5)
    self.commentsGrid.set_row_spacing(0.5 * self.defaultFontSize)

    scroller_comments = Gtk.ScrolledWindow()
    scroller_comments.add(self.commentsGrid)

    vbox_commentsArea = Gtk.VBox()
    vbox_commentsArea.pack_start(hbox_addCommentButton, False, False, 0)
    vbox_commentsArea.pack_start(scroller_comments, True, True, 0)

    expander_customComments.add(vbox_commentsArea)


    ################
    # Custom tags. #
    ################

    expander_customTags = Gtk.Expander(label = "Custom tags (TXXX)")
    expander_customTags.set_resize_toplevel(True)

    # Button for adding new comments.
    self.addCustomTagButton = Gtk.Button(label = "Add new custom tag", image = Gtk.Image.new_from_icon_name("list-add", 4), hexpand = False, margin_bottom = 0.5 * self.defaultFontSize)
    self.addCustomTagButton.set_sensitive(False)
    self.addCustomTagButton.connect("clicked", self.addCustomTagLine)

    hbox_addCustomTagButton = Gtk.HBox()
    hbox_addCustomTagButton.pack_start(Gtk.Label(), True, True, 0)
    hbox_addCustomTagButton.pack_start(self.addCustomTagButton, False, False, 0)
    
    self.customTagsGrid = Gtk.Grid(margin = 0.5 * self.defaultFontSize)#, margin_bottom = 0.5 * self.defaultFontSize)
    self.customTagsGrid.set_column_spacing(5)
    self.customTagsGrid.set_row_spacing(0.5 * self.defaultFontSize)

    scroller_customTags = Gtk.ScrolledWindow()
    scroller_customTags.add(self.customTagsGrid)

    vbox_customTagsArea = Gtk.VBox()
    vbox_customTagsArea.pack_start(hbox_addCustomTagButton, False, False, 0)
    vbox_customTagsArea.pack_start(scroller_customTags, True, True, 0)

    expander_customTags.add(vbox_customTagsArea)
    

    #frame_extendedTags = Gtk.Frame()
    #frame_extendedTags.add(vbox_extendedTags)

    #######################
    # The revert buttons. #
    #######################

    hbox_revertButtons = Gtk.HBox(homogeneous = True, margin_top = 0.5 * self.defaultFontSize, spacing = 5)

    self.revertTagsOfThisFileButton = Gtk.Button(label = "Revert all tags of this file", image = Gtk.Image.new_from_icon_name("edit-undo", 4))
    self.revertTagsOfThisFileButton.set_sensitive(False)
    self.revertTagsOfThisFileButton.connect("clicked", self.revertTagsOfThisFile)
    hbox_revertButtons.pack_start(self.revertTagsOfThisFileButton, True, True, 0)

    self.revertTagsOfAllFilesButton = Gtk.Button(label = "Revert tags of all files", image = Gtk.Image.new_from_icon_name("document-revert", 4))
    self.revertTagsOfAllFilesButton.set_sensitive(False)
    self.revertTagsOfAllFilesButton.connect("clicked", self.revertTagsOfAllFiles)
    hbox_revertButtons.pack_start(self.revertTagsOfAllFilesButton, True, True, 0)
    
    # The write-to-file buttons.
    hbox_writeChangesButton = Gtk.HBox(homogeneous = True, margin_top = 0.5 * self.defaultFontSize, spacing = 5)

    self.writeChangesToThisFileButton = Gtk.Button(label = "Write changes to this file", image = Gtk.Image.new_from_icon_name("document-save", 4))
    self.writeChangesToThisFileButton.set_sensitive(False)
    self.writeChangesToThisFileButton.connect("clicked", self.writeChangesToThisFile)
    hbox_writeChangesButton.pack_start(self.writeChangesToThisFileButton, True, True, 0)

    self.writeAllChangesButton = Gtk.Button(label = "Write all changes", image = Gtk.Image.new_from_icon_name("document-save-all", 4))
    self.writeAllChangesButton.set_sensitive(False)
    self.writeAllChangesButton.connect("clicked", self.writeAllChanges)
    hbox_writeChangesButton.pack_start(self.writeAllChangesButton, True, True, 0)

    vbox_defaultAndExtendedTags = Gtk.VBox(spacing = 5)
    vbox_defaultAndExtendedTags.pack_start(hbox_coverAndDefaultTags, False, False, 0)
    vbox_defaultAndExtendedTags.pack_start(Gtk.HSeparator(margin_top = 0.5 * self.defaultFontSize), False, False, 0)

    vbox_defaultAndExtendedTags.pack_start(expander_extendedTags, False, False, 0)
    vbox_defaultAndExtendedTags.pack_start(expander_customComments, False, False, 0)
    vbox_defaultAndExtendedTags.pack_start(expander_customTags, True, True, 0)

    #vbox_defaultAndExtendedTags.pack_start(vpaned_extendedCommentsCustoms, True, True, 0)

    vbox_defaultAndExtendedTags.pack_start(Gtk.HSeparator(margin_top = 0.5 * self.defaultFontSize), False, False, 0)
    vbox_defaultAndExtendedTags.pack_start(hbox_revertButtons, False, False, 0)
    vbox_defaultAndExtendedTags.pack_start(hbox_writeChangesButton, False, False, 0)
    
    vbox_tags.pack_start(vbox_defaultAndExtendedTags, True, True, 0)

    frame_defaultAndExtendedTags = Gtk.Frame()
    frame_defaultAndExtendedTags.add(vbox_tags)
    
    # Composing the final main box.
    hbox_main.pack1(vbox_fileListAndRename, True, False)
    hbox_main.pack2(frame_defaultAndExtendedTags, True, False)
    
    self.add(hbox_main)

    self.populateFileListFromArguments()

    self.show_all()

    self.connect("destroy", Gtk.main_quit)

    self.populateFileListFromPathList(songs)

    Gtk.main()


  def clearCoverArt(self, button):
    index = self.getSelectedFileIndex()
    #TAGDATA['new'][index]['APIC'] = mutagen.id3.APIC()
    if "APIC" in TAGDATA['new'][index]:
      TAGDATA['new'][index].pop("APIC")
    self.setCoverArt(sysPath.join(BASEDIR, "noCover.png"))
    self.tagRevertButtonAPIC.set_sensitive(True)
    self.clearCoverButton.set_sensitive(False)


  def revertTag(self, button, tag):
    index = self.getSelectedFileIndex()
    print("Reverting " + tag + " of file " + str(index))
    if tag in TAGDATA['new'][index]:
      TAGDATA['new'][index].pop(tag) 
    if tag == "APIC":
      if "APIC" in TAGDATA['current'][index]:
        self.setCoverArt(TAGDATA['current'][index]['APIC'].data)
        self.tagRevertButtonAPIC.set_sensitive(False)
        self.clearCoverButton.set_sensitive(True)
      else:
        self.setCoverArt(sysPath.join(BASEDIR, "noCover.png"))
        self.tagRevertButtonAPIC.set_sensitive(False)
    else:
      getattr(self, "tagEntry" + tag).set_text(str(TAGDATA['current'][index][tag]))
      # No need to delete TAGDATA['new'][index][tag] here as it happens right after setting the new text because of the noteTageChange method.


  def revertTagInEveryFile(self, button, tag):
    pass


  def revertTagsOfThisFile(self, button):
    selectedIndex = self.getSelectedFileIndex()
    for k in TAGDATA["current"][selectedIndex].keys():
      if k in TAGDATA["new"][selectedIndex].keys() and not k == "APIC":
        value = TAGDATA["current"][selectedIndex][k]
        if hasattr(value, "text"):
          getattr(self, "tagEntry" + k).set_text("; ".join(value.text))
          # After this operation self.noteTagChange deletes the corresponing value in the TAGDATA["new"] dictionary, because both values are identical.
        else:
          print("WARNING: No text attribute in frame ", k)

    # Remove tags that have been newly created but not committed yet.
    for k in TAGDATA["new"][selectedIndex].keys():
      if not k == "APIC":
        TAGDATA["new"][selectedIndex].pop(k)


  def revertTagsOfAllFiles(self, button):
    selectedIndex = self.getSelectedFileIndex()
    for f in TAGDATA["current"]:
      for k in TAGDATA["current"][f].keys():
        if k in TAGDATA["new"][f].keys() and not k == "APIC":
          value = TAGDATA["current"][f][k]
          if f == selectedIndex:
            if hasattr(value, "text"):
              getattr(self, "tagEntry" + k).set_text("; ".join(value.text))
              # After this operation self.noteTagChange deletes the corresponing value in the TAGDATA["new"] dictionary, because both values are identical.
            else:
              print("WARNING: No text attribute in frame ", k)
          else:
            TAGDATA["new"][f].pop(k)

    self.revertTagsOfAllFilesButton.set_sensitive(False)
    self.writeAllChangesButton.set_sensitive(False)


  def writeChangesToThisFile(self):
    pass


  def writeAllChanges(self):
    pass


  def addFilesToFileList(self, button):
    fileChooser = Gtk.FileChooserDialog()
    fileChooser.set_select_multiple(True)

    fileFilter = Gtk.FileFilter()
    fileFilter.add_pattern("*.mp3")
    fileChooser.set_filter(fileFilter)

    fileChooser.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

    fileChooser.show()

    response = fileChooser.run()
    if response == Gtk.ResponseType.OK:
      self.fileListStore.clear()
      self.populateFileListFromPathList(fileChooser.get_filenames())

    print(TAGDATA["new"])

    fileChooser.destroy()


  def noteTagChange(self, entry, tagName):
    print("noteTagChange")
    selectedFileIndex = self.getSelectedFileIndex()

    # Current tag might be empty, so it has to be created if it does not exist yet.
    if not tagName in TAGDATA["current"][selectedFileIndex]:
      TAGDATA["current"][selectedFileIndex][tagName] = getattr(mutagen.id3, tagName)()
      print("CREATED NEW TAG STRUCTURE ", type(getattr(mutagen.id3, tagName)()))
    currentText = TAGDATA["current"][selectedFileIndex][tagName]
    newText = entry.get_text()

    if tagName == "TCON":
      newText = re.sub(r" *; *", ";", newText).split(";")

    if hasattr(self, "tagRevertButton" + tagName):
      if newText != currentText:
        TAGDATA["new"][selectedFileIndex][tagName] = newText
        getattr(self, "tagRevertButton" + tagName).set_sensitive(True)
      else:
        if tagName in TAGDATA["new"][selectedFileIndex]:
          TAGDATA["new"][selectedFileIndex].pop(tagName)
        getattr(self, "tagRevertButton" + tagName).set_sensitive(False)

    if "TRCK" in TAGDATA['new'][selectedFileIndex]:
      print("TRCK", TAGDATA['new'][selectedFileIndex]["TRCK"].text)

    if len(TAGDATA['new'][selectedFileIndex]) > 0:
      self.revertTagsOfThisFileButton.set_sensitive(True)
      self.revertTagsOfAllFilesButton.set_sensitive(True)
      self.writeChangesToThisFileButton.set_sensitive(True)
      self.writeAllChangesButton.set_sensitive(True)
    else:
      self.revertTagsOfThisFileButton.set_sensitive(False)
      self.writeChangesToThisFileButton.set_sensitive(False)
      self.revertTagsOfAllFilesButton.set_sensitive(False)
      self.writeAllChangesButton.set_sensitive(False)
      for k in TAGDATA["new"]:
        if len(TAGDATA["new"][k]) > 0:
          self.revertTagsOfAllFilesButton.set_sensitive(True)
          self.writeAllChangesButton.set_sensitive(True)
          break

    self.updateFileNamePreview(None)


  def renameSelectedFile(self, button):
    pass


  def renameAllFiles(self, button):
    pass


  def addCommentLine(self, button):
    if len(self.commentsGrid) == 0:
      languageLabel = Gtk.Label(label = "Language")
      languageLabel.set_tooltip_text("ISO-639-2, three letters")
      self.commentsGrid.attach(languageLabel, 0, len(self.commentsGrid) / 4, 1, 1)
      self.commentsGrid.attach(Gtk.Label(label = "Description"), 1, len(self.commentsGrid) / 4, 1, 1)
      self.commentsGrid.attach(Gtk.Label(label = "Comment"), 2, len(self.commentsGrid) / 4, 1, 1)
      self.commentsGrid.attach(Gtk.Label(), 3, len(self.commentsGrid) / 4, 1, 1)

    commentLang = Gtk.Entry(hexpand = True, width_chars = 3, max_length = 3)
    commentDesc = Gtk.Entry(hexpand = True)
    commentText = Gtk.Entry(hexpand = True)

    deleteCommentButton = Gtk.Button.new_from_icon_name("edit-delete", 4)
    deleteCommentButton.connect("clicked", self.deleteCommentLine)
    
    self.commentsGrid.attach(commentLang, 0, len(self.commentsGrid) / 4, 1, 1)
    self.commentsGrid.attach(commentDesc, 1, len(self.commentsGrid) / 4, 1, 1)
    self.commentsGrid.attach(commentText, 2, len(self.commentsGrid) / 4, 1, 1)
    self.commentsGrid.attach(deleteCommentButton, 3, len(self.commentsGrid) / 4, 1, 1)

    self.commentsGrid.show_all()


  def addCustomTagLine(self, button):
    if len(self.customTagsGrid) == 0:
      self.customTagsGrid.attach(Gtk.Label(label = "Description"), 0, 0, 1, 1)
      self.customTagsGrid.attach(Gtk.Label(label = "Text"), 1, 0, 1, 1)
      self.customTagsGrid.attach(Gtk.Label(), 2, 0, 1, 1)

    customTagDesc = Gtk.Entry(hexpand = True)
    customTagText = Gtk.Entry(hexpand = True)

    deleteCustomTagButton = Gtk.Button.new_from_icon_name("edit-delete", 4)
    deleteCustomTagButton.connect("clicked", self.deleteCustomTagLine)

    print(self.customTagsGrid.get_children())
    
    self.customTagsGrid.attach(customTagDesc, 0, len(self.customTagsGrid) / 3, 1, 1)
    self.customTagsGrid.attach(customTagText, 1, len(self.customTagsGrid) / 3, 1, 1)
    self.customTagsGrid.attach(deleteCustomTagButton, 2, len(self.customTagsGrid) / 3, 1, 1)

    self.customTagsGrid.show_all()


  def copyTagValueToAllFiles(self, button, tag):
    print("Copying " + tag + " to other files …")
    selectedIndex = self.getSelectedFileIndex()
    dataOrigin = 'new' if tag in TAGDATA['new'][selectedIndex] else 'current'
    if tag == "APIC":
      for k in TAGDATA['current']:
        TAGDATA['new'][k][tag] = getattr(mutagen.id3, tag)()
        TAGDATA['new'][k][tag].data = TAGDATA[dataOrigin][selectedIndex][tag].data
        if tag in TAGDATA['current'][k] and TAGDATA['new'][k][tag].data == TAGDATA['current'][k][tag].data:
          TAGDATA['new'][k].pop(tag)
    else:
      for k in TAGDATA['current']:
        TAGDATA['new'][k][tag] = getattr(mutagen.id3, tag)()
        TAGDATA['new'][k][tag].text = TAGDATA[dataOrigin][selectedIndex][tag].text
        if tag in TAGDATA['current'][k] and TAGDATA['new'][k][tag].text[0] == TAGDATA['current'][k][tag].text[0]:
          TAGDATA['new'][k].pop(tag)


  def getSelectedFileIndex(self):
    model, path = self.fileListTreeview.get_selection().get_selected_rows()
    if path:
      selectedIndex = path[0].get_indices()[0]
      return self.fileListStore[selectedIndex][0]
    else:
      return -1



  def enumerateOtherTracks(self, button):
    model, path = self.fileListTreeview.get_selection().get_selected_rows()
    selectedFileIndex = path[0].get_indices()[0]

    dataOrigin = "new" if "TRCK" in TAGDATA["new"][selectedFileIndex] else "current"

    ordinalNumbers = re.findall("([0-9]+)/?([0-9]*)", str(TAGDATA[dataOrigin][selectedFileIndex]['TRCK']))
    print("Number", ordinalNumbers)
    if len(ordinalNumbers) > 0:
      for i in range(selectedFileIndex + 1, len(model)):
        if not "TRCK" in TAGDATA['new'][i]:
          TAGDATA['new'][i]["TRCK"] = mutagen.id3.TRCK()
        TAGDATA["new"][i]["TRCK"].text = [str(int(ordinalNumbers[0][0]) + i - selectedFileIndex) + ("/" + str(ordinalNumbers[0][1]) if ordinalNumbers[0][1] != "" else "")]

        if TAGDATA["new"][i]["TRCK"] == TAGDATA["current"][i]["TRCK"]:
          del TAGDATA["new"][i]["TRCK"]
        else:
          self.revertTagsOfAllFilesButton.set_sensitive(True)
          self.writeAllChangesButton.set_sensitive(True)
          

  def deleteExtendedTag(self, button):
    for i in range(int(len(self.tagsGrid_extended) / 3)):
      if self.tagsGrid_extended.get_child_at(2, i) == button:
        deletedFrame = self.tagsGrid_extended.get_child_at(0, i).get_label()
        deletedDescription = self.tagsGrid_extended.get_child_at(0, i).get_tooltip_text()
        self.tagsGrid_extended.remove_row(i)
        model, path = self.fileListTreeview.get_selection().get_selected_rows()
        selectedIndex = path[0].get_indices()[0]        
        if deletedFrame in TAGDATA['new'][selectedIndex]:
          del TAGDATA['new'][selectedIndex][deletedFrame]
        break

    if hasattr(self, 'childWindow'):
      alreadyUsedFrames = []
      for i in range(int(len(self.tagsGrid_extended) / 3)):
        alreadyUsedFrames.append(self.tagsGrid_extended.get_child_at(0, i).get_label())

      # Delete all the entries in the list of frames in the child window …
      while len(self.childWindow.tagStore) > 0:
        self.childWindow.tagStore.remove(self.childWindow.tagStore.get_iter(0))

      # … and re-add all frames …
      for i in range(len(frameList)):
        # … that aren’t already present in the parent window.
        if not frameList[i][0] in alreadyUsedFrames:        
          self.childWindow.tagStore.append([frameList[i][0] + " (" + frameList[i][1] + ")"])
      
    else:
      print("Child window closed")


  def deleteCommentLine(self, button):
    for i in range(int(len(self.commentsGrid) / 4)):
      if self.commentsGrid.get_child_at(3, i) == button:
        self.commentsGrid.remove_row(i)
        break

    if len(self.commentsGrid) == 4:
      self.commentsGrid.remove_row(0)


  def deleteCustomTagLine(self, button):
    for i in range(int(len(self.customTagsGrid) / 3)):
      if self.customTagsGrid.get_child_at(2, i) == button:
        self.customTagsGrid.remove_row(i)
        break

    if len(self.customTagsGrid) == 3:
      self.customTagsGrid.remove_row(0)


  def selectedFileChanged(self, selection):
    # Reset the extended tags.
    while len(self.tagsGrid_extended) > 0:
      self.tagsGrid_extended.remove_row(0)
  
    # Reset the comments.
    while len(self.commentsGrid) > 0:
      self.commentsGrid.remove_row(0)

    # Reset the custom tags.
    while len(self.customTagsGrid) > 0:
      self.customTagsGrid.remove_row(0)

    selectedIndex = self.getSelectedFileIndex()

    if selectedIndex == -1:
      self.renameSelectedFileButton.set_sensitive(False)
      self.renameAllFilesButton.set_sensitive(False)
      self.fileNamePattern.set_sensitive(False)    
    else:
      self.renameSelectedFileButton.set_sensitive(True)
      self.renameAllFilesButton.set_sensitive(True)
      self.fileNamePattern.set_sensitive(True)

      for t in [entry for entry in dir(self) if entry.startswith("tagEntry")]:
        getattr(self, t).set_sensitive(True)

      for t in [entry for entry in dir(self) if entry.startswith("tagCopyButton")]:
        getattr(self, t).set_sensitive(True)
    
      self.addExtendedTagsButton.set_sensitive(True)
      self.addCustomTagButton.set_sensitive(True)
      self.addCommentButton.set_sensitive(True)
    
      extendedTagEntries = {}
      for i in range(int(len(self.tagsGrid_extended) / 2)):
        extendedTagLabel = self.tagsGrid_extended.get_child_at(0, i).get_label().replace(":", "")
        extendedTagEntries[extendedTagLabel] = self.tagsGrid_extended.get_child_at(1, i)
    
      #print("MERGING ", list(TAGDATA['current'][selectedIndex].keys()))
      #print("AND ", list(TAGDATA['new'][selectedIndex].keys()))
    
      mergedTagsList = list(TAGDATA['current'][selectedIndex].keys()) + list(TAGDATA['new'][selectedIndex].keys())
    
      print("TAG DATA IN SELECTION: ", TAGDATA['new'])
    
      if "APIC" in mergedTagsList:
        print("APIC FOUND IN LIST")
        dataOrigin = 'new' if "APIC" in TAGDATA['new'][selectedIndex] else 'current'
        if dataOrigin == 'new':
          if TAGDATA[dataOrigin][selectedIndex]["APIC"].data == b'':
            self.setCoverArt(sysPath.join(BASEDIR, "noCover.png"))
          else:
            self.setCoverArt(TAGDATA[dataOrigin][selectedIndex]["APIC"].data)
            self.clearCoverButton.set_sensitive(True)
          self.tagRevertButtonAPIC.set_sensitive(True)
        else:
          self.setCoverArt(TAGDATA[dataOrigin][selectedIndex]["APIC"].data)
          self.clearCoverButton.set_sensitive(True)
          self.tagRevertButtonAPIC.set_sensitive(False)
      else:
        print("NO APIC")
        self.setCoverArt(sysPath.join(BASEDIR, "noCover.png"))
        print(self.clearCoverButton.get_sensitive())
    
      for tag in mergedTagsList:
        #currentTagsTemp[tag] = TAGDATA['current'][selectedIndex][tag]
        #print(type(TAGDATA['current'][selectedIndex][tag]).__name__)
    
        dataOrigin = 'new' if tag in TAGDATA['new'][selectedIndex] else 'current'
    
        if dataOrigin == 'new':
          if hasattr(self, "tagRevertButton" + tag):
            getattr(self, "tagRevertButton" + tag).set_sensitive(True)
        else:
          if hasattr(self, "tagRevertButton" + tag):
            getattr(self, "tagRevertButton" + tag).set_sensitive(False)
    
        if tag == "TPE1" or tag == "TIT2" or tag == "TALB" or tag == "TRCK" or tag == "TPOS":
          if hasattr(TAGDATA[dataOrigin][selectedIndex][tag], "text"):
            getattr(self, "tagEntry" + tag).set_text("; ".join(TAGDATA[dataOrigin][selectedIndex][tag].text))
          else:
            getattr(self, "tagEntry" + tag).set_text(TAGDATA[dataOrigin][selectedIndex][tag])
          #pass
    
        elif tag == "TCON":
          if hasattr(TAGDATA[dataOrigin][selectedIndex][tag], "text"):
            getattr(self, "tagEntry" + tag).set_text("; ".join(TAGDATA[dataOrigin][selectedIndex][tag].text))
          else:
            getattr(self, "tagEntry" + tag).set_text("; ".join(TAGDATA[dataOrigin][selectedIndex][tag]))
        
        elif tag == "TDRL": # Check, if MPD can handle TDRL tag.
          tmpList = list(TAGDATA[dataOrigin][selectedIndex][tag].text)
          for i in range(0, len(tmpList)):
            tmpList[i] = str(tmpList[i])
          getattr(self, "tagEntry" + tag).set_text("; ".join(tmpList))
    
        elif tag == "COMM":
          for i in range(len(TAGDATA[dataOrigin][selectedIndex][tag])):
            self.addCommentButton.emit("clicked")
            self.commentsGrid.get_child_at(0, len(self.commentsGrid) / 4 - 1).set_text(TAGDATA[dataOrigin][selectedIndex][tag][i]['lang'])
            self.commentsGrid.get_child_at(1, len(self.commentsGrid) / 4 - 1).set_text(TAGDATA[dataOrigin][selectedIndex][tag][i]['desc'])
            self.commentsGrid.get_child_at(2, len(self.commentsGrid) / 4 - 1).set_text(TAGDATA[dataOrigin][selectedIndex][tag][i]['text'])
    
        elif tag == "TXXX":
          for i in range(len(TAGDATA[dataOrigin][selectedIndex][tag])):
            self.addCustomTagButton.emit("clicked")
            self.customTagsGrid.get_child_at(0, len(self.customTagsGrid) / 3 - 1).set_text(TAGDATA[dataOrigin][selectedIndex][tag][i]['desc'])
            self.customTagsGrid.get_child_at(1, len(self.customTagsGrid) / 3 - 1).set_text(TAGDATA[dataOrigin][selectedIndex][tag][i]['text'])
    
        elif tag == "APIC":
          pass
    
        else:
          print("Extended tag: ", TAGDATA[dataOrigin][selectedIndex][tag], type(TAGDATA[dataOrigin][selectedIndex][tag]))
          if any(tag in f for f in frameList):
            self.addExtendedTag(tag, None, str(TAGDATA[dataOrigin][selectedIndex][tag].text[0]))
          #extendedTagEntries[tag].set_text(TAGDATA[dataOrigin][selectedIndex][tag].text[0])

    print("SENSITIVE: ", self.clearCoverButton.get_sensitive())


  def getTagData(self, filePath):
    returnDict = {}
    data = MP3(filePath)

    print("DATA", data)
    
    #for d in data:
    #  print("CHECKING", d)
    #  #print(data[d])
    #  #if d != "APIC:":
    #    #print(type(data[d]))
    #  d_stripped = re.match("^[^:]+", d).group()
    #  if d_stripped == "COMM":
    #    print(data[d].text, data[d].lang, data[d].desc)
    #    if d_stripped in returnDict:
    #      returnDict[d_stripped].append({"text" : data[d].text[0], "lang" : data[d].lang, "desc" : data[d].desc})
    #    else:
    #      returnDict[d_stripped] = [{"text" : data[d].text[0], "lang" : data[d].lang, "desc" : data[d].desc}]
    #  elif d_stripped == "TXXX":
    #    print(data[d].text, data[d].desc)
    #    if d_stripped in returnDict:
    #      returnDict[d_stripped].append({"text" : data[d].text[0], "desc" : data[d].desc})
    #    else:
    #      returnDict[d_stripped] = [{"text" : data[d].text[0], "desc" : data[d].desc}]
    #  else:
    #    returnDict[d_stripped] = data[d]
    #  #print(data[d])

    #print("DICTIONARY: ", returnDict, ", ", type(returnDict["TDRC"].text[0]))
    #return returnDict
    return data


  def populateFileListFromArguments(self):
    newList = []
    args = sys.argv
    for i in range(1, len(args)):
      fullPath = sysPath.abspath(args[i])
      if sysPath.isfile(fullPath):
        if re.match(r".*\.mp3$", fullPath):
          newList.append(fullPath)
        else:
          print("— " + args[i] + " is no valid mp3 file.")
      else:
        print("— " + args[i] + " is a path. Searching for mp3 files …")
        searchPath = sysPath.abspath(args[i])
        potentialFiles = listdir(searchPath)
        for f in listdir(searchPath):
          fullPath = sysPath.join(searchPath, f)
          if sysPath.isfile(fullPath):
            if re.match(r".*\.mp3$", f):
              newList.append(fullPath)
            else:
              print("— " + f + " is no valid mp3 file.")
    newList.sort()
    self.populateFileListFromPathList(newList)
    

  def populateFileListFromPathList(self, pathsList):
    TAGDATA['current'] = {}
    TAGDATA['new'] = {}
    for filePath in pathsList:
      fileName = filePath.split("/")[-1]
      self.fileListStore.append([filePath, fileName])
      tagData = self.getTagData(filePath)
      TAGDATA['current'][filePath] = tagData
      TAGDATA['new'][filePath] = {}

    if len(pathsList) > 0:
      self.fileListTreeview.set_cursor(Gtk.TreePath.new_from_indices([0]))
      self.fileListTreeview.grab_focus()

      # Enable all applicable buttons.


  def coverArtFrameChangedSize(self, widget, rectangle):
    print("COVER ART FRAME CHANGED ITS SIZE")
    imageInside = widget.get_children()[0]
    imageProps = imageInside.get_pixbuf().props
    print("RESOURCE", imageInside.props)
    #widget.set_size_request(max(rectangle.width, rectangle.height), max(rectangle.width, rectangle.height))
    frameMargin = min(rectangle.width - imageProps.width, rectangle.height - imageProps.height)
    targetSize = 0
    if rectangle.width - imageProps.width == frameMargin:
      targetSize = rectangle.height
    else:
      targetSize = rectangle.width

    

    #if imageProps.width < imageProps.height:
    #  imageInside.get_pixbuf().scale_simple(-1, targetSize - frameMargin, 2)
    #else:
    #  imageInside.get_pixbuf().scale_simple(targetSize - frameMargin, -1, 2)

    selectedIndex = self.getSelectedFileIndex()

    print(selectedIndex)

    print("TARGET SIZE: ", targetSize)

    #widget.set_size_request(targetSize, targetSize)

    #if selectedIndex == -1:
    #  if imageProps.width > imageProps.height:
    #    self.setCoverArt(sysPath.join(BASEDIR, "noCover.png"), targetSize - frameMargin - 1, -1)
    #  else:
    #    self.setCoverArt(sysPath.join(BASEDIR, "noCover.png"), -1, targetSize - frameMargin - 1)

    
      
    print("Frame margin: ", min(rectangle.width - imageProps.width, rectangle.height - imageProps.height))
    print("Image height: ", imageInside.get_pixbuf().props.height)
    print(rectangle.width)
    print(widget.get_children())
    print(Gtk.Settings.get_default())
    print(widget.do_compute_child_allocation(widget, rectangle))


  def setCoverArt(self, imageData, targetWidth = -1, targetHeight = None):
    if not targetHeight:
      targetHeight = 24 * self.defaultFontSize

    print("SETTING IMAGE SIZE: ", targetWidth, ", ", targetHeight)
    if type(imageData) == str:
      pixbuf = Pixbuf.new_from_file_at_scale(imageData, targetWidth, targetHeight, True)
      #print("Default font size: " + str(self.defaultFontSize))
      self.coverArt.set_from_pixbuf(pixbuf)
    else:
      imgObject = io.BytesIO(imageData).read()
      glibBytes = GLib.Bytes.new(imgObject)
      imgDataStream = Gio.MemoryInputStream.new_from_bytes(glibBytes)
      pixbuf = Pixbuf.new_from_stream_at_scale(imgDataStream, targetWidth, targetHeight, True, None)
      #pixbuf = Pixbuf.new_from_stream(imgDataStream)
      self.coverArt.set_from_pixbuf(pixbuf)
    
    #print("Pixbuf size: " + str(pixbuf.get_width()) + ", " + str(pixbuf.get_height()))
    #print("Margins (left, right, top, bottom): " + str(int((24 * self.defaultFontSize - pixbuf.get_width()) / 2) + 0.5 * self.defaultFontSize) + ", " + str(25 * self.defaultFontSize - imageWidget.get_margin_start() - pixbuf.get_width()) + ", " + str(int((24 * self.defaultFontSize - pixbuf.get_height()) / 2) + 0.5 * self.defaultFontSize) + ", " + str(25 * self.defaultFontSize - imageWidget.get_margin_top() - pixbuf.get_height()))

    #imageWidget.set_margin_start( int((24 * self.defaultFontSize - pixbuf.get_width()) / 2) + 0.5 * self.defaultFontSize)
    #imageWidget.set_margin_end( 25 * self.defaultFontSize - imageWidget.get_margin_start() - pixbuf.get_width()) 
    #imageWidget.set_margin_start(0)
    #imageWidget.set_margin_end(0) 
    #imageWidget.set_margin_top( int((24 * self.defaultFontSize - pixbuf.get_height()) / 2) + 0.5 * self.defaultFontSize )
    #imageWidget.set_margin_bottom( 25 * self.defaultFontSize - imageWidget.get_margin_top() - pixbuf.get_height()) 
    #imageWidget.set_margin_top(0)   
    #imageWidget.set_margin_bottom(0)

  def chooseCoverArt(self, button):
    pass


  def updateFileNamePreview(self, entry):
    selectedIndex = self.getSelectedFileIndex()
    entryText = self.fileNamePattern.get_text()
    if entryText == "":
      self.fileNamePreview.set_text("No pattern to evaluate.")
      self.renameSelectedFileButton.set_sensitive(False)
      self.renameAllFilesButton.set_sensitive(False)
    else:
      # Enable using key words instead of frame names for tag replacements.
      tagMap = generalTagsList + [["Track", "TRCK"], ["Disc", "TPOS"]]
      for t in tagMap:
        entryText = entryText.replace("[%" + t[0] + "]", "[%" + t[1] + "]")
      # Replace all frame names with the data saved for the file.
      potentialTagPlaceholders = re.findall(r"\[%([^]]+)\]", entryText)
      for p in potentialTagPlaceholders:
        if p in TAGDATA['new'][selectedIndex]:
          entryText = entryText.replace("[%" + p + "]", TAGDATA['new'][selectedIndex][p])
        elif p in TAGDATA['current'][selectedIndex]:
          entryText = entryText.replace("[%" + p + "]", str(TAGDATA['current'][selectedIndex][p].text[0]))
      self.fileNamePreview.set_text(entryText + ".mp3")

      # Iterate over all files and check for duplicate file names.
      newFileNames = []
      for file in TAGDATA["current"]:
        fileName = self.fileNamePattern.get_text()
        for t in tagMap:
          fileName = fileName.replace("[%" + t[0] + "]", "[%" + t[1] + "]")
        potentialTagPlaceholders = re.findall(r"\[%([^]]+)\]", fileName)
        for p in potentialTagPlaceholders:
          if p in TAGDATA['new'][file]:
            fileName = fileName.replace("[%" + p + "]", TAGDATA['new'][file][p])
          elif p in TAGDATA['current'][file]:
            fileName = fileName.replace("[%" + p + "]", str(TAGDATA['current'][file][p].text[0]))

        if fileName in newFileNames:
          self.hbox_renameWarning.props.opacity = 1.0
          self.renameSelectedFileButton.set_sensitive(False)
          self.renameAllFilesButton.set_sensitive(False)
        else:
          self.hbox_renameWarning.props.opacity = 0.0
          self.renameSelectedFileButton.set_sensitive(True)
          self.renameAllFilesButton.set_sensitive(True)
          newFileNames.append(fileName)
          


  def openExtendedTagsList(self, button):
    self.addExtendedTagsButton.handler_block(self.addExtendedTagsButton_connectID)
    self.childWindow = extendedTagsListWindow(self)


  def addExtendedTag(self, tag = None, description = None, value = None):
    tagLabel = Gtk.Label(label = tag, xalign = 0)
    if not description:
      for i in range(len(frameList)):
        if frameList[i][0] == tag:
          description = frameList[i][1]
          break
    tagLabel.set_tooltip_text(description)
    self.tagsGrid_extended.attach(tagLabel, 0, len(self.tagsGrid_extended) / 3, 1, 1)
    tagEntry = Gtk.Entry(hexpand = True)
    tagEntry.connect("changed", self.noteTagChange, tag)
    if value:
      tagEntry.set_text(value)
    self.tagsGrid_extended.attach(tagEntry, 1, len(self.tagsGrid_extended) / 3, 1, 1)
    deleteExtendedTagButton = Gtk.Button.new_from_icon_name("edit-delete", 4)
    deleteExtendedTagButton.connect("clicked", self.deleteExtendedTag)
    self.tagsGrid_extended.attach(deleteExtendedTagButton, 2, len(self.tagsGrid_extended) / 3, 1, 1)
    self.tagsGrid_extended.show_all()



#############################################
# Separate window for adding extended tags. #
#############################################

class extendedTagsListWindow(Gtk.Window):
  def __init__(self, parent):
    super().__init__()

    self.set_default_icon_name("id3v2-editor")
    self.set_title("Add extended ID3 tag")
    self.set_default_size(1, 400)
    self.set_transient_for(parent)
    self.set_position(4)
    self.connect("destroy", self.quit, parent)

    self.tagsFilterEntry = Gtk.Entry()
    self.tagsFilterEntry.connect("changed", self.resetFilter)
    self.tagsFilterEntry.set_placeholder_text("Filter")

    vbox_main = Gtk.VBox(spacing = 5, margin = 5)
    vbox_main.pack_start(self.tagsFilterEntry, False, False, 0)


    ##############################################

    self.tagStore = Gtk.ListStore(str)

    # Get the list of already present ID3 frames in the parent window.
    alreadyUsedFrames = []
    for i in range(int(len(parent.tagsGrid_extended) / 3)):
      alreadyUsedFrames.append(parent.tagsGrid_extended.get_child_at(0, i).get_label())

    for i in range(len(frameList)):
      # Add only the frames that aren’t already present in the parent window.
      if not frameList[i][0] in alreadyUsedFrames:        
        self.tagStore.append([frameList[i][0] + " (" + frameList[i][1] + ")"])#, xalign = 0)


    def filter_func(model, iter, data):
      alreadyUsedFrames = []
      for i in range(int(len(parent.tagsGrid_extended) / 3)):
        alreadyUsedFrames.append(parent.tagsGrid_extended.get_child_at(0, i).get_label())
      if re.findall("^[^ ]+", model[iter][0])[0] in alreadyUsedFrames:
        return False
      else:
        return self.tagsFilterEntry.get_text().lower() in model[iter][0].lower()


    self.tagFilter = self.tagStore.filter_new()
    self.tagFilter.set_visible_func(filter_func)

    self.tagTreeView = Gtk.TreeView(model = self.tagFilter)
    self.tagTreeView.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

    renderer = Gtk.CellRendererText()
    column = Gtk.TreeViewColumn("Frame", renderer, text = 0)
    self.tagTreeView.append_column(column)

    tagsListScroller = Gtk.ScrolledWindow()
    tagsListScroller.add(self.tagTreeView)
    #tagsListScroller.set_size_request(400, 1)
    
    vbox_main.pack_start(tagsListScroller, True, True, 0)

    addSelectedTagsButton = Gtk.Button(label = "Add selected tags")
    addSelectedTagsButton.connect("clicked", self.addSelectedTagsToMainWindow, parent)

    vbox_main.pack_start(addSelectedTagsButton, False, False, 0)
    
    self.add(vbox_main)

    self.show_all()

    tagsListScroller.set_size_request(self.tagTreeView.get_preferred_width().minimum_width + 10, 1)
    self.set_size_request(tagsListScroller.get_allocated_size()[0].width, 1)


  def addSelectedTagsToMainWindow(self, button, parent):
    model, path = self.tagTreeView.get_selection().get_selected_rows()
    for p in path:
      index = p.get_indices()[0]
      fullLabelText = model.get_value(model.get_iter(index), 0)
      id3tag = re.findall("^[^ ]+", fullLabelText)[0]
      tagDescription = re.findall(r".*\((.+)\)$", fullLabelText)[0]
      parent.addExtendedTag(id3tag, None)
      # To do: Delete the actual index in the ListStore, not the displayed and potentially filtered one.
      self.resetFilter(self)
      #self.tagStore.remove(self.tagStore.get_iter(index))


  def resetFilter(self, a):
    self.tagFilter.refilter()


  def quit(self, _, parent):
    parent.addExtendedTagsButton.handler_unblock(parent.addExtendedTagsButton_connectID)
    del parent.childWindow


def main():
  tagEditor(None)


if __name__ == "__main__":
  main()


