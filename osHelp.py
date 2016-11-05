import sys
import os
import platform
import locale
import codecs

from subprocess import *

from logger import log

class osHelper:
    """Helper class to check for topojson"""
    
    def __init__(self):
        """Constructor"""
        self.__logger = log(self.__class__.__name__)
        
        self.platform = platform.system()
        self.isWindows = False
        self.helper = linuxHelper()
                
        self.__logger.info(platform.system())
        
        if platform.system() == "Windows":
            self.isWindows = True
            self.helper = winHelper() 
                
class linuxHelper:
    """Linux OS class for performing topojson commands"""
        
    def __init__(self):
        """Constructor. Nothing special here"""
        self.__logger = log(self.__class__.__name__)
        
    def hasTopojson(self):
        """Does this OS have topojson installed?
        
        :returns: Whether the topojson is installed  
        :rtype: bool  
        """
        success = False
        
        try:
            result = check_output(["which", "topojson"])
            
            self.__logger.info("which result " + result) 
            
            success = True             
        
        except CalledProcessError:
            
            self.__logger.error2()           
            
        return success
    
    def output(self, folder, out, name, shapefile, quantization, simplification, idProperty, properties):
        """Output the shapefile as topojson, with a specific name, and simplification level
        
        :param folder: Folder to output the topojson file.
            Assumed that this folder has been created outside of this class
        :type folder: str
        
        :param out: Name of the resulting topojson file. 
            ".json" will be added automatically as a suffix 
        :type out: str
        
        :param name: resulting topology.objects name.
        :type name: str
        
        :param shapefile: Path to the ESRI shapefile.
        :type shapefile: str
        
        :param quantization: Maximum number of differentiable points along either dimension.
        :type quantization: str
        
        :param simplification: Precision threshold as string.
        :type simplification: str
        
        :param idProperty: Name of feature property to promote to geometry id.
        :type idProperty: str
        
        :param properties: Feature properties to preserve.
        :type properties: list  
              
        :returns: The message from topojson  
        :rtype: string         
        """
        result = ""

        args = []
        args.append("topojson")
        args.append("-o")
        args.append(os.path.join(folder, out + ".json"))
        if len(idProperty) > 0:
            args.append("--id-property")
            args.append(idProperty)
        if len(properties) > 0:
            args.append("-p")
            args.append(",".join(properties))
        if len(quantization) > 0:
            args.append("-q")
            args.append(quantization)
        if len(simplification) > 0:
            args.append("-s")
            args.append(simplification)
        args.append("--")
        if len(name) > 0:
            args.append(name + "=" + shapefile)
        else:
            args.append(shapefile)
        
        self.__logger.info(" ".join(args)) 
        
        result = check_output(args, stderr=STDOUT)
        
        self.__logger.info("topojson result " + result)              
            
        return result
    
class winHelper(linuxHelper):
    """Windows OS class for performing topojson commands
    
        Windows requires extra messing around to call topojson (or any other npm package) from python"""
    
    def __init__(self):
        """Constructor"""
        self.node = ""
        self.topojs = ""
        self.__logger = log(self.__class__.__name__) 
        self.reg = __import__("_winreg")     
    
    def hasTopojson(self):
        """TopoJson check in windows is a complicated mess
        
        :returns: Whether the topojson is installed  
        :rtype: bool  
        """
        
        nodeFound = self.getNodeJsPath()
        topoFound = False
        if nodeFound:
            # No point in doing this if nodeJS not installed, as the npm command will fail
            topoFound = self.getTopoJsonPath()
            
        return nodeFound and topoFound
    
    def output(self, folder, out, name, shapefile, quantization, simplification, idProperty, properties):
        """Output the shapefile as topojson, with a specific name, and simplification level
        
        :param folder: Folder to output the topojson file.
            Assumed that this folder has been created outside of this class
        :type folder: str
        
        :param out: Name of the resulting topojson file. 
            ".json" will be added automatically as a suffix 
        :type out: str
        
        :param name: resulting topology.objects name.
        :type name: str
        
        :param shapefile: Path to the ESRI shapefile.
        :type shapefile: str        
        
        :param quantization: Maximum number of differentiable points along either dimension.
        :type quantization: str
        
        :param simplification: Precision threshold as string.
        :type simplification: str
        
        :param idProperty: Name of feature property to promote to geometry id.
        :type idProperty: str
        
        :param properties: Feature properties to preserve.
        :type properties: list 
        
        :returns: The message from topojson  
        :rtype: string       
        """
        result = ""

        if self.hasTopojson() == True:
            args = []
            args.append(self.node)
            args.append(self.topojs)
            args.append("-o")
            args.append(os.path.join(folder, out + ".json"))
            if len(idProperty) > 0:
                args.append("--id-property")
                args.append(idProperty)
            if len(properties) > 0:
                args.append("-p")
                args.append(",".join(properties))
            if len(quantization) > 0:
                args.append("-q")
                args.append(quantization)
            if len(simplification) > 0:
                args.append("-s")
                args.append(simplification)
            args.append("--")
            if len(name) > 0:
                args.append(name + "=" + shapefile)
            else:
                args.append(shapefile)
            
            self.__logger.info(" ".join(args)) 
                 
            result = check_output(args, stderr=STDOUT, shell=True)
            
            self.__logger.info("topojson result \r\n" + result)               
            
        return result
    
    def getNodeJsPath(self):
        """Attempt to get the install location of nodejs"""
        
        # NodeJs could be installed anywhere and called anything so can't rely on 
        # Try the Current User InstallPath
        subname = os.path.normpath("Software/node.js")
        valName = "InstallPath"
        found = False
        try:
            # Query the registry...
            self.__logger.info("Query registry for " + os.path.join("HKEY_CURRENT_USER", subname, valName))
            subkey = self.reg.OpenKey(self.reg.HKEY_CURRENT_USER, subname)
            
            i = 0
            while 1:
                name, value, type = self.reg.EnumValue(subkey, i)
                if name == valName:
                    self.node = os.path.join(value, "node.exe")
                    self.__logger.info("node.js found at " + self.node)
                    found = True
                    break
                
                i += 1
        except WindowsError as e:
            self.__logger.error(e.args[1] + ": " + subname)
        
        if found == False:
            # Later versions of the Node.JS installer have removed the previous location 
            # in favour of the local machine  installed software  
            subname = os.path.normpath("SOFTWARE/node.js")
            try:
                # Query the registry...
                self.__logger.info("Query registry for " + os.path.join("HKEY_LOCAL_MACHINE", subname, valName))
                subkey = self.reg.OpenKey(self.reg.HKEY_LOCAL_MACHINE, subname)
                
                i = 0
                while 1:
                    name, value, type = self.reg.EnumValue(subkey, i)
                    if name == valName:
                        self.node = os.path.join(value, "node.exe")
                        self.__logger.info("node.js found at " + self.node)
                        found = True
                        break
                    
                    i += 1
            except WindowsError as e:
                self.__logger.error(e.args[1] + ": " + subname)                
                
                
        
        
        
        return found
        
    
    def getTopoJsonPath(self):
        """Attempt to get the topojson  package installation location"""
        
        # Node Package Manager could be installed anywhere
        # Look in the PATH user environment variable
        subname = "Environment"
        valName = "PATH"
        npm = os.path.normpath("/npm")
        topopkg = os.path.normpath("node_modules/topojson/bin/topojson")
        found = False
        try:
            # Query the registry...
            self.__logger.info("Query registry for " + os.path.join("HKEY_CURRENT_USER", subname, valName))
            subkey = self.reg.OpenKey(self.reg.HKEY_CURRENT_USER, subname)
            
            i = 0
            while 1:
                name, value, type = self.reg.EnumValue(subkey, i)
                if name == valName:
                    self.__logger.info("User environment variables: " + value)
                    paths = value.split(";")
                    for p in paths:
                        # Is this the /npm value?
                        if p.endswith(npm):
                            self.topojs = os.path.join(p, topopkg)
                            self.__logger.info("topojson found at " + self.topojs)
                            found = True
                            break
                    break
                
                i += 1
                
        except WindowsError as e:
            self.__logger.error(e.args[1] + ": " + subname)
            
        return found            