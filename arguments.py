class ScriptArguments():
    
  def __init__(self, address = '', protocol = 'ipp', queueName = '', displayName = '', name = '', location = '', ipp = 'everywhere', defaultCatalog = 'testing', defaultCategory = 'Printers', defaultDeveloper = 'Printers',version = '0.1', options = []):
    self.__address=address
    self.__protocol=protocol
    self.__queueName=queueName
    self.__displayName=displayName
    self.__name=name
    self.__location=location
    self.__ipp=ipp
    self.__defaultCatalog=defaultCatalog
    self.__defaultCategory=defaultCategory
    self.__defaultDeveloper=defaultDeveloper
    self.__version=version
    self.__options=options
    
    
  def getAddress(self) -> str: 
    return self.__address

  def setAddress(self, address): 
    self.__address = address

  def getProtocol(self) -> str: 
    return self.__protocol

  def setProtocol(self, protocol): 
    self.__protocol = protocol

  def getQueueName(self) -> str: 
    return self.__queueName

  def setQueueName(self, queueName): 
    self.__queueName = queueName

  def getDisplayName(self) -> str: 
    return self.__displayName

  def setDisplayName(self, displayName): 
    self.__displayName = displayName

  def getName(self) -> str: 
    return self.__name

  def setName(self, name): 
    self.__name = name

  def getLocation(self) -> str: 
    return self.__location

  def setLocation(self, location): 
    self.__location = location

  def getIpp(self) -> str: 
    return self.__ipp

  def setIpp(self, ipp): 
    self.__ipp = ipp
  
  def getDefaultCatalog(self) -> str: 
    return self.__defaultCatalog

  def setDefaultCatalog(self, defaultCatalog): 
    self.__defaultCatalog = defaultCatalog

  def getDefaultCategory(self) -> str: 
    return self.__defaultCategory

  def setDefaultCategory(self, defaultCategory): 
    self.__defaultCategory = defaultCategory

  def getDefaultDeveloper(self) -> str: 
    return self.__defaultDeveloper

  def setDefaultDeveloper(self, defaultDeveloper): 
    self.__defaultDeveloper = defaultDeveloper

  def getOptions(self) -> list: 
    return self.__options

  def setOptions(self, options): 
    self.__options = options

  def appendOption(self, option): 
    self.__options.append(option)

  def getVersion(self) -> str: 
    return self.__version

  def setVersion(self, version): 
    self.__version = version

  def getXmlKeyMapping(self):
    return {
      "protocol": 'setProtocol',
      "address": 'setAddress',
      "queue_name": 'setQueueName',
      "name": 'setName',
      "display_name": 'setDisplayName',
      "location": 'setLocation',
      "options": 'setOptions',
      "ipp": 'setIpp',
      "default_catalog": 'setDefaultCatalog',
      "default_category": 'setDefaultCategory',
      "default_developer": 'setDefaultDeveloper',
      "version": 'setVersion',
    }

  def fromDictionary(self, dictionary):
    xmlKeys = self.getXmlKeyMapping()
    for key in dictionary:
      functionName = xmlKeys.get(key)
      if(functionName):
        function = getattr(self, functionName)
        function(dictionary[key])
    return self

  def __str__(self):
    return "address=" + str(self.__address) + ", protocol=" +str(self.__protocol) + ", queuename=" +str(self.__queueName) + ", displayname=" +str(self.__displayName) + ", name=" +str(self.__name) + ", location=" +str(self.__location) + ", ipp=" +str(self.__ipp) + ", options=" +str(self.__options)




