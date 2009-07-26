#!/usr/bin/python

from pyjamas import Window
from pyjamas.ui.RootPanel import RootPanel
from pyjamas.ui.Button import Button

def greet(sender):
    Window.alert("Hello, AJAX!")

if __name__ == '__main__':
    b = Button("Click me", greet)
    RootPanel().add(b)
