# sl2util
> Automation Common Tasks - Logger & ConfigData.

_v1.2.1 on Python3.8 & Python3.9_

On this project, I pretend to handle all the libs commonly shared across 
all the automation projects.

Modules:

configdatareader:

    -- Generate a Key with a password
    -- Read a Decrypted xml File
    -- Encrypt and Save the xml file 
    -- Keep data on dictionary for any time usage

logger:

    -- create and handle log files
    -- as an alternative to the logging lib
    
dbhandler

    -- Connection to Oracle/MSSQL
    -- Retrieve Table, SingleRow
    -- Set Insert, updates, SPs
    
utils

    -- Mail sender
    -- Text parser
    
This project is part of the common L2System packages for automation.

## Installation

Windows:

Download file ``_./dist/sl2util-1.0.0.tar.gz_`` and unzip the file.
On ``cmd`` get to the root of unzipped dir and run:
```sh
python setup.py install
```

## Usage example

To read a xml config file and crypt.

_For more examples and usage, please refer to the [Docs][Docs]._
```python
import sl2util.configdatareader as cryptlib
# Get Basic Info
BASE_FILE = os.path.basename(sys.argv[0])
BASE_PATH = os.getcwd()
KeyPassword = input('Personal KeyPassword:')
DecFile = input('Decoded xml ProjectFile Name(./):')
key = cryptlib.get_key(KeyPassword.encode())
# Get Info to CryptoLib
cryptlib.set_key(key)
cryptlib.setDecFilePath(BASE_PATH + '\\' + DecFile, True)
cryptlib.setEncFilePath(BASE_PATH + '\\' + 'enc' + DecFile, True)
# Make the xml ProjectFile encoded
cryptlib.encodeXML(False)
```
## Development setup

Just download the project locally and run the test at ``./tests``.

```sh
python util.py
```

## Release History

* 1.2.1
    * ADDED: Watchdog handler for services
* 1.0.5
    * ADDED: Level1 Handler (OPC-UA connection).
* 1.0.3
    * ADDED: utils, Mail sender and a text parser
* 1.0.1
    * ADDED: DataBase Handler
* 1.0.0
    * RELEASE: Packaged and available (module code remains unchanged)
    * CHANGE: Project Layout as standard
* 0.0.1
    * Work in progress

## Meta

Sergio Chavez Rangel – steel.l2.automation@gmail.com

Distributed under the MIT license. See ``LICENSE`` for more information.

[SergioChavez@Github](https://github.com/SergioChavezRangel/)


<!-- Markdown link & img dfn's -->
[Docs]: https://github.com/SergioChavezRangel/SL2Utilities-master/tree/master/tests