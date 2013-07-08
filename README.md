randterm
========

<img src="https://raw.github.com/randvoorhies/randterm/master/OSX_Screenshot.png"></img>

An open source full featured serial terminal written in Python

RandTerm was created mainly to help debug microcontroller serial protocols, and
so includes the ability to display and send data in Ascii, Decimal,
Hexadecimal, or Binary formats. It is written as a single Python file, and has
been tested in Linux and OS X. There is a pre-packaged version for OS
X available in the downloads section that has absolutely no prerequisites.

## Getting RandTerm

### Linux

- Install pySerial and wxPython on your system, e.g. in Ubuntu:

```{bash}
sudo apt-get install python-wxgtk2.8 
sudo apt-get install python-serial
```

- Check out the project using the svn link in the Source section of this site..
- Run RandTerm!:

```{bash}
python randterm
```

### OS X

- Getting wxPython to work in OS X is a bit of a pain.
  - Followed the instructions [here](http://batok.github.com/virtualenvwxp/) to get wxPython running.
  - Install pySerial:

```{bash}
pip install pySerial 
```

- Check out the project using the svn link in the Source section of this site.
- Run RandTerm:

```{bash}
pythonw randterm 
```

## Usage

- Set your connection settings using the Connect menu.
  - Your connection settings will be saved by the application and restored whenever the RandTerm is opened
- Click the Connect button, or use the Connect->Open Connection menu item to open the port
- Choose your display format using the RX Format radio buttons above the main display area
  - Changing the RX Format with a lot of data in in the display buffer might take a second because RandTerm needs to reconvert all of the raw data for display.
- Send data over the serial connection:
  - Using the LiveType area will directly forward all keystrokes immediately to the serial port, including carriage returns, etc.
  - By using the numbered TX fields below the LiveType you can send individual bytes to the serial terminal.
    - When the TX Format is Decimal, Hex, or Binary each space separated byte will be sent in sequence when you hit the enter key.
    - When the TX Format is Ascii, each letter will be send in sequence when you hit the enter key.
- The bytes you send will be shown in blue, while the received bytes will be shown in red.
- That's it! Have fun, and let me know how it goes.

## Helping Out

There are a ton of improvements to RandTerm that I don't have time to make
right now, so if you're any good at hacking Python and have a few spare hours
I could use the help. And who knows - if you write a ton of code, we might even
rename the project RandJakeTerm? (or whatever your name is). Let me know if
you're interested: rand dot voorhies at gmail dot com.
