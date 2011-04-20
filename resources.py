from pyglet import resource, media, image
import os
import string

class Resource:

    def __init__(self):

        self.sound_dict = {}
        self.image_dict = {}

        self.image_filetypes = ('.jpg', '.gif', '.bmp', '.png')
        self.sound_filetypes = ('.wav', '.mp3')
        
        self.filetypes = []
        self.filetypes.extend(self.image_filetypes)
        self.filetypes.extend(self.sound_filetypes)

    def load_directory(self, path):

        resource.path.append(path)
        print resource.path
        osPath = ''
        for _ in resource.path:
            osPath += _
            osPath += os.sep
        osPath = osPath[:-1]
        print osPath
        dirList = os.listdir(osPath)
            
        print "Entering directory %s.\n" % path
        resource.reindex()
        for fname in dirList:
            ext = ''
            print fname
            if string.rfind(fname,".") != -1:
                name = fname[:string.rfind(fname,".")]
                ext = fname[string.rfind(fname,"."):]
            else:
                name = fname
            print "name = %s" % name
            print "ext = %s" % ext
            if ( ext ) and (ext in self.filetypes):
                self.load_file(name, ext, osPath)
            if not ext:
                self.load_directory(name)
        print "Leaving directory %s.\n" % resource.path.pop()

    def load_file(self, name, ext, path):
        if ext in self.image_filetypes:
            self.image_dict[name + ext] = image.load(os.path.join(path, 
                '%s%s' % (name, ext))).get_texture()
            print "Image '%s' loaded!" % (name + ext)
        if ext in self.sound_filetypes:
            self.sound_dict[name + ext] = media.load(path + os.sep + name + ext,
                                                     streaming = False)
            print "Sound '%s' loaded!" % (name + ext)
