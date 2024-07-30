#Imports modules which are to be used in the system
import smtplib, hashlib, secrets, re, sqlite3, mplcursors, customtkinter as ctk, matplotlib.pyplot as plt, matplotlib.dates as mdates
from tkinter import messagebox
from PIL import Image
from datetime import datetime, timedelta
from ttkbootstrap.dialogs import Querybox
from ttkbootstrap.dialogs.colorchooser import ColorChooserDialog

#Connects to the database and creates a cursor
conn = sqlite3.connect('rfid')
cursor = conn.cursor()

theme_color = '#ff7e75'
#This uses customtkinter's CTk class to create a window.
window = ctk.CTk()
#Sets the title of the window
window.title('RFID System')
#Sets the geometry
window.geometry('600x600')
#Restricting the x and y geometry of the screen to not be resizable.
window.resizable(False, False)
#Creating a window frame that sits on top of the actual window to give the window a border and a theme colour to add style.
window_frame = ctk.CTkFrame(window, fg_color = theme_color, corner_radius = 0, border_color = 'black', border_width = 2)
#This places the frame on the window and expands and fills everything from corner to corner.
window_frame.pack(expand = True, fill = 'both')
#By default customtkinter uses dark mode and my program is going to be in light mode since it is used during school hours.
#This sets the customtkiner appearance mode to light.
ctk.set_appearance_mode('light')

#A class which stores the details of the user.
class User:
    def __init__(self, user_id, first_name, last_name, hashed_password, salt, grade, facility_id):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.hashed_password = hashed_password
        self.salt = salt
        self.grade = grade
        self.facility_id = facility_id
    
#A class which stores the details of the user's card.
class Card:
    def __init__(self, card_id, tag_id):
        self.card_id = card_id
        self.tag_id = tag_id

#A class which inherits a frame from the customtkinter module which uses multiple bookings to replicate the same object with a few differences.
class OutgoingApprovalSegment(ctk.CTkFrame):
    #A constructor method which defines itself, where the frame will be sitting on top off, the specific booking and it's corresponding object.
    def __init__(self, parent, booking, status, outgoing_approval_objects):
        #A super constructor method which defines the frame's attributes from which this class inherits from.
        super().__init__(master = parent, border_color = "black", border_width = 2, corner_radius = 0, fg_color = '#F0F0F0')
        self.booking = booking
        self.outgoing_approval_objects = outgoing_approval_objects
        #Creating a 1 dimensional grid to display the booking.
        self.rowconfigure(0, weight = 1)
        self.columnconfigure((0, 1, 2, 3, 4, 5, 6), weight = 1)
        facility = booking[1]
        if facility == 'Multi-Purpose Hall':
            facility = 'MPH'
        #Each widget is a value from the record.
        ctk.CTkButton(self, text = facility, width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 0)
        ctk.CTkButton(self, text = self.booking[2], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 1)
        ctk.CTkButton(self, text = self.booking[3], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 2)
        if booking[4] == 'Wednesday':
            ctk.CTkButton(self, text = self.booking[4], width = 100, height = 30, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 15), hover = False, corner_radius = 0).grid(row = 0, column = 3)
        else:
            ctk.CTkButton(self, text = self.booking[4], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 3)        
        ctk.CTkButton(self, text = self.booking[5], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 4)
        ctk.CTkButton(self, text = status, width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 5)
        if status != 'Approved':
            close_button = ctk.CTkImage(light_image = Image.open("Images/close.png"), size = (22,22))
            ctk.CTkButton(self, text = '', image = close_button, width = 10, hover_color = '#F0F0F0', fg_color = '#d4d4d4', bg_color = '#d4d4d4', command = self.remove_booking,).grid(row = 0, column = 6)
        self.pack(pady = 10)

    #A method which carries out the backend process of removing the request.
    def remove_booking(self):
        #These two line updates the record to set the status to False from the previous Null value in both the Booking and Timeslot table.
        cursor.execute('UPDATE Timeslot SET status = FALSE WHERE timeslot_id = ?', (self.booking[7],))
        cursor.execute('DELETE FROM Booking WHERE booking_number = ?', (self.booking[0],))
        conn.commit()
        self.delete_approval_object()

    #A method which deletes the approval object and remove it from the bookings array.
    def delete_approval_object(self):
        #Cycles through every object in the objects array.
        for approval_object in self.outgoing_approval_objects:
            #Checks if the object has the same user id as the bookings user id.
            if approval_object.booking[0] == self.booking[0]:
                #Cycles through every widget in the frame and destroys it.
                for widget in approval_object.winfo_children():
                    widget.destroy()
                #Removes the object from the object array.
                self.outgoing_approval_objects.remove(approval_object)
                #Deletes the object entirely.
                del approval_object 

#A class which inherits a frame from the customtkinter module which is used multiple timings to replicate the same object with a few differences.
class IncomingApprovalSegment(ctk.CTkFrame):
    #A constructor method which defines itself, where the frame will be sitting on top off, the specific booking and it's corresponding object.
    def __init__(self, parent, incoming_approval_objects, booking, card):
        #A super constructor method which defines the frame's attributes from which this class inherits from.
        super().__init__(master = parent)
        self.card = card
        self.incoming_approval_objects = incoming_approval_objects
        self.booking = booking
        self.toplevel_window = None
        #Creating a 1 dimensional grid to display the request.
        self.rowconfigure(0, weight = 1)
        self.columnconfigure((0, 1, 2, 3, 4, 5), weight = 1)
        #Images files are loaded for accepting or declining.
        close_button = ctk.CTkImage(light_image = Image.open("Images/close.png"), size = (22,22))
        check_button = ctk.CTkImage(light_image = Image.open("Images/check.png"), size = (22,22))
        facility = booking[1]
        if facility == 'Multi-Purpose Hall':
            facility = 'MPH'
        #Each widget is a value from the record.
        ctk.CTkButton(self, text = self.booking[11], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover_color = '#d4d4d4', corner_radius = 0, command = self.open_toplevel).grid(row = 0, column = 0)
        ctk.CTkButton(self, text = facility, width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 1)
        ctk.CTkButton(self, text = self.booking[2], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 2)
        ctk.CTkButton(self, text = self.booking[3], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 3)
        if booking[4] == 'Wednesday':
            ctk.CTkButton(self, text = self.booking[4], width = 100, height = 30, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 15), hover = False, corner_radius = 0).grid(row = 0, column = 4)
        else:
            ctk.CTkButton(self, text = self.booking[4], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 4)
        ctk.CTkButton(self, text = self.booking[5], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 5)
        ctk.CTkButton(self, text = '', image = check_button, width = 10, hover_color = '#F0F0F0', fg_color = '#d4d4d4', bg_color = '#d4d4d4', command = self.accept_booking).grid(row = 0, column = 8)
        ctk.CTkButton(self, text = '', image = close_button, width = 10, hover_color = '#F0F0F0', fg_color = '#d4d4d4', bg_color = '#d4d4d4', command = self.decline_booking).grid(row = 0, column = 9)
        self.pack(pady = 10)

    #A method which carries out the backend process of accepting a request.
    def accept_booking(self):
        #These two line updates the record to set the status to True from the previous Null value in both the Booking and Timeslot table.
        cursor.execute('UPDATE Timeslot SET status = TRUE WHERE timeslot_id = ?', (self.booking[7],))
        cursor.execute('UPDATE Booking SET approved = TRUE WHERE booking_number = ?', (self.booking[0],))
        conn.commit()
        #Calls the method.
        self.delete_approval_object()

    #A method which carries out the backend process of declining a request.
    def decline_booking(self):
        #These two line updates the record to set the status to False from the previous Null value in both the Booking and Timeslot table.
        cursor.execute('UPDATE Timeslot SET status = FALSE WHERE timeslot_id = ?', (self.card.card_id,))
        cursor.execute('UPDATE Booking SET approved = FALSE WHERE booking_number = ?', (self.booking[0],))
        conn.commit()
        #Calls the method.
        self.delete_approval_object()

    #A method which deletes the approval object and remove it from the bookings array.
    def delete_approval_object(self):
        #Cycles through every object in the objects array.
        for approval_object in self.incoming_approval_objects:
            #Checks if the object has the same user id as the bookings user id.
            if approval_object.booking[0] == self.booking[0]:
                #Cycles through every widget in the frame and destroys it.
                for widget in approval_object.winfo_children():
                    widget.destroy()
                #Removes the object from the object array.
                self.incoming_approval_objects.remove(approval_object)
                #Deletes the object entirely.
                del approval_object 

    #A method which creates a pop-up window.
    def open_toplevel(self):
        #Checks if the pop up window exists or not.
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            #Creates the pop up window with the StudentProfile class.
            self.toplevel_window = StudentProfile(self.booking, self.card)
            self.toplevel_window.focus()
        else:
            self.toplevel_window.focus()

#A class which inherits a frame from the customtkinter module which uses multiple bookings to replicate the same object with a few differences.
class ScheduledBookingSegment(ctk.CTkFrame):
    #A constructor method which defines itself, where the frame will be sitting on top off and the details of the user and their card along with info of the booking and its objects.
    def __init__(self, parent, booking_objects, booking, card, user):
        #A super constructor method which defines the frame's attributes from which this class inherits from.
        super().__init__(master = parent)
        self.booking_objects = booking_objects
        self.user = user
        self.card = card
        self.booking = booking
        #Creating a 1 dimensional grid to display the booking.
        self.rowconfigure(0, weight = 1)
        self.columnconfigure((0, 1, 2, 3, 4, 5, 6), weight = 1)
        facility = booking[1]
        if facility == 'Multi-Purpose Hall':
            facility = 'MPH'
        #Widgets
        ctk.CTkButton(self, text = self.booking[11], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover_color = '#d4d4d4', corner_radius = 0, command = self.open_toplevel).grid(row = 0, column = 0)
        ctk.CTkButton(self, text = facility, width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 1)
        ctk.CTkButton(self, text = self.booking[2], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 2)
        ctk.CTkButton(self, text = self.booking[3], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 3)
        if booking[4] == 'Wednesday':
            ctk.CTkButton(self, text = self.booking[4], width = 100, height = 30, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 15), hover = False, corner_radius = 0).grid(row = 0, column = 4)
        else:
            ctk.CTkButton(self, text = self.booking[4], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 4)
        ctk.CTkButton(self, text = self.booking[5], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 5)
        self.toplevel_window = None
        #Checks whether the an admin access this page.
        if self.user.user_id[0] == 'A':
            #Loads an extra button to remove the booking.
            close_button = ctk.CTkImage(light_image = Image.open("Images/close.png"), size = (22,22))
            ctk.CTkButton(self, text = '', image = close_button, width = 10, hover_color = '#F0F0F0', fg_color = '#d4d4d4', bg_color = '#d4d4d4', command = self.decline_booking).grid(row = 0, column = 6)
        self.pack(pady = 10)
    
    #A method which carries out the backend process of removing a booking.
    def decline_booking(self):
        #These two line updates the record to set the status to False from the previous True value in both the Booking and Timeslot table.
        cursor.execute('UPDATE Timeslot SET status = FALSE WHERE timeslot_id = ?', (self.card.card_id,))
        cursor.execute('UPDATE Booking SET approved = FALSE WHERE booking_number = ?', (self.booking[0],))
        conn.commit()
        self.delete_booking_object()

    #A method which deletes the approval object and remove it from the bookings array.
    def delete_booking_object(self):
        #Cycles through every object in the objects array.
        for booking_object in self.booking_objects:
            #Checks if the object has the same user id as the bookings user id. 
            if booking_object.booking[0] == self.booking[0]:
                #Cycles through every widget in the frame and destroys it.
                for widget in booking_object.winfo_children():
                    widget.destroy()
                #Removes the object from the object array.
                self.booking_objects.remove(booking_object)
                #Deletes the object entirely.
                del booking_object 
  
    #A method which creates a pop-up window.
    def open_toplevel(self):
        #Checks if the pop up window exists or not.
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            #Creates the pop up window with the StudentProfile class.
            self.toplevel_window = StudentProfile(self.booking, self.card)
            self.toplevel_window.focus()
        else:
            self.toplevel_window.focus()

#A class which inherits a top level window from the customtkinter module which displays the students info to the teacher or admin.
class StudentProfile(ctk.CTkToplevel):
    #A constructor method which defines itself and takes in the booking information along with the card information of the user.
    def __init__(self, booking, card, *args, **kwargs):
        #This allows the arguments to be passed on to this class and is able to be modified.
        super().__init__(*args, **kwargs)

        #Basic Window setup.
        self.geometry("300x300")
        self.title('Student Info')
        self.resizable(False, False)

        #A window and info frame is created in order to match the aesthetics of the program.
        window_frame = ctk.CTkFrame(self, width = 300, height = 300, border_color = 'black', border_width = 2, fg_color = theme_color, corner_radius = 0)
        window_frame.place(anchor = 'center', relx = 0.5, rely = 0.5)

        info_frame = ctk.CTkFrame(self, width = 250, height = 250, border_color = 'black', border_width = 2, fg_color = '#F0F0F0', corner_radius = 0)
        info_frame.place(anchor = 'center', relx = 0.5, rely = 0.5)
        info_frame.rowconfigure(0, weight = 1)
        info_frame.columnconfigure((0, 1, 2, 3, 4), weight = 1)

        #Widgets
        title_font = ctk.CTkFont(family = 'Impact', size = 18, underline = True)
        info_font = ctk.CTkFont(family = 'Impact', size = 18)
        ctk.CTkLabel(info_frame, text = 'User ID:', font = title_font).place(anchor = 'e', relx = 0.5, rely = 0.1)
        ctk.CTkLabel(info_frame, text = 'Card ID:', font = title_font).place(anchor = 'e', relx = 0.5, rely = 0.3)
        ctk.CTkLabel(info_frame, text = 'First Name:', font = title_font).place(anchor = 'e', relx = 0.5, rely = 0.5)
        ctk.CTkLabel(info_frame, text = 'Last Name:', font = title_font).place(anchor = 'e', relx = 0.5, rely = 0.7)
        ctk.CTkLabel(info_frame, text = 'Class:', font = title_font).place(anchor = 'e', relx = 0.5, rely = 0.9)
        ctk.CTkLabel(info_frame, text = booking[11], font = info_font).place(anchor = 'w', relx = 0.53, rely = 0.1)
        ctk.CTkLabel(info_frame, text = card.card_id, font = info_font).place(anchor = 'w', relx = 0.53, rely = 0.3)
        ctk.CTkLabel(info_frame, text = booking[8], font = info_font).place(anchor = 'w', relx = 0.53, rely = 0.5)
        ctk.CTkLabel(info_frame, text = booking[9], font = info_font).place(anchor = 'w', relx = 0.53, rely = 0.7)
        ctk.CTkLabel(info_frame, text = booking[10], font = info_font).place(anchor = 'w', relx = 0.53, rely = 0.9)

#A class which inherits a frame from the customtkinter module which uses multiple records to replicate the same object with a few differences.
class Records(ctk.CTkFrame):
    #A constructor method which defines itself, where the frame will be sitting on top off along with the record and its objects.
    def __init__(self, parent, user, record, records):
        #A super constructor method which defines the frame's attributes from which this class inherits from.
        super().__init__(master = parent, border_color = "black", border_width = 2, corner_radius = 0, fg_color = '#F0F0F0')
        self.records = records
        self.user = user
        self.record = record
        #Creating a 1 dimensional grid to display the booking.
        self.rowconfigure(0, weight = 1)
        self.columnconfigure((0, 1, 2, 3, 4, 5), weight = 1)
        #Widgets
        ctk.CTkButton(self, text = self.record[0], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 0)
        ctk.CTkButton(self, text = self.record[1], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 1)
        ctk.CTkButton(self, text = self.record[2], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 2)
        ctk.CTkButton(self, text = self.record[3], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 3)
        ctk.CTkButton(self, text = self.record[4], width = 100, border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 18), hover = False, corner_radius = 0).grid(row = 0, column = 4)
        #Checks whether an admin is accessing the page and shows the remove button accordingly. 
        if self.user.user_id[0] == 'A':
            close_button = ctk.CTkImage(light_image = Image.open("Images/close.png"), size = (22,22))
            ctk.CTkButton(self, text = '', image = close_button, width = 10, hover_color = '#F0F0F0', fg_color = '#d4d4d4', bg_color = '#d4d4d4', command = self.remove_record).grid(row = 0, column = 8)
        self.pack(pady = 10)
    
    def remove_record(self):
        #Resets the card the user had, ready for the next user to come and register.
        cursor.execute('UPDATE CARD SET user_id = NULL WHERE user_id = ?', (self.record[0],))
        #Deletes the record off the database.
        cursor.execute('DELETE FROM User WHERE user_id = ?', (self.booking[0],))
        conn.commit()
        self.remove_record_objects()

    #A method to remove the object from the associates array and delete its object.
    def remove_record_objects(self):
        for record in self.records: 
            if record.record[0] == self.records[0]:
                for widget in record.winfo_children():
                    widget.destroy()
                self.records.remove(record)
                del record

#A class which inherits a frame from the customtkinter module
class ContentFrame(ctk.CTkFrame):
    #A constructor method which defines itself, where the frame will be sitting on top off and the details of the user and their card.
    def __init__(self, parent, user, card):
        #A super constructor method which defines the frame's attributes from which this class inherits from.
        super().__init__(parent, width = 650, height = 550, border_color = "black", border_width = 2, corner_radius = 0, fg_color = '#F0F0F0')
        #Defining the user and card to allow use in the whole class.
        self.user = user
        self.card = card
        #A label indicating the user with a welcome message
        ctk.CTkLabel(self, text = 'Welcome!', font = ('Impact', 140)).place(anchor = 'center', relx = 0.5, rely = 0.5)

#Account Info View and Password Change
    #A method to display the user's information and edit their password.
    def account_edit_page(self):
        self.clear_frame()
        #Variables
        self.password_entry = ctk.StringVar()
        self.confirm_password_entry = ctk.StringVar()
        heading_font = ctk.CTkFont(family = 'Impact', size = 75, underline = True)
        title_font = ctk.CTkFont(family = 'Impact', size = 40, underline = True)
        info_font = ctk.CTkFont(family = 'Impact', size = 40)
        #Widgets
        ctk.CTkLabel(self, text = 'Profile', font = heading_font).place(anchor = 'center', relx = 0.5, rely = 0.15)
        ctk.CTkLabel(self, text = 'First Name:', font = title_font).place(anchor = 'center', relx = 0.2, rely = 0.33)
        ctk.CTkLabel(self, text = self.user.first_name, font = info_font).place(anchor = 'center', relx = 0.5, rely = 0.33)
        if self.user.user_id[0] == 'A':
            ctk.CTkLabel(self, text = 'User ID:', font = title_font).place(anchor = 'center', relx = 0.2, rely = 0.48)
            ctk.CTkLabel(self, text = self.user.user_id, font = info_font).place(anchor = 'center', relx = 0.5, rely = 0.48)
            ctk.CTkLabel(self, text = 'Card ID:', font = title_font).place(anchor = 'center', relx = 0.2, rely = 0.63)    
            ctk.CTkLabel(self, text = self.card.card_id, font = info_font).place(anchor = 'center', relx = 0.5, rely = 0.63)           
        elif self.user.user_id[0] == 'T' or self.user.user_id[0] == 'S':
            ctk.CTkLabel(self, text = 'Last Name:', font = title_font).place(anchor = 'center', relx = 0.2, rely = 0.48)
            ctk.CTkLabel(self, text = self.user.last_name, font = info_font).place(anchor = 'center', relx = 0.5, rely = 0.48)
            ctk.CTkLabel(self, text = 'User ID:', font = title_font).place(anchor = 'center', relx = 0.2, rely = 0.78)
            ctk.CTkLabel(self, text = self.user.user_id, font = info_font).place(anchor = 'center', relx = 0.5, rely = 0.78)
            ctk.CTkLabel(self, text = 'Card ID:', font = title_font).place(anchor = 'center', relx = 0.2, rely = 0.93)    
            ctk.CTkLabel(self, text = self.card.card_id, font = info_font).place(anchor = 'center', relx = 0.5, rely = 0.93)      
            if self.user.user_id[0] == 'T':
                facility_name = cursor.execute('SELECT facility_name FROM Facility WHERE facility_id = ?', (self.user.facility_id,)).fetchall()
                ctk.CTkLabel(self, text = 'Facility:', font = title_font).place(anchor = 'center', relx = 0.2, rely = 0.63)
                ctk.CTkLabel(self, text = facility_name, font = info_font).place(anchor = 'center', relx = 0.5, rely = 0.63)
            else:
                ctk.CTkLabel(self, text = 'Class:', font = title_font).place(anchor = 'center', relx = 0.2, rely = 0.63)
                ctk.CTkLabel(self, text = self.user.grade, font = info_font).place(anchor = 'center', relx = 0.5, rely = 0.63)
        ctk.CTkLabel(self, text = 'New Password', font = ('Impact', 20)).place(anchor = 'center', relx = 0.8, rely = 0.38)
        ctk.CTkEntry(self, textvariable = self.password_entry, width = 190, border_color = 'black', border_width = 2, corner_radius = 0).place(anchor = 'center', relx = 0.8, rely = 0.43)
        ctk.CTkLabel(self, text = 'Confirm Password', font = ('Impact', 20)).place(anchor = 'center', relx = 0.8, rely = 0.58)
        ctk.CTkEntry(self, textvariable = self.confirm_password_entry, width = 190, border_color = 'black', border_width = 2, corner_radius = 0).place(anchor = 'center', relx = 0.8, rely = 0.63)
        ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', text = 'Update', font = ('Impact', 20), command = self.account_edit_func).place(anchor = 'center', relx = 0.8, rely = 0.78)    
        ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', text = 'Update', font = ('Impact', 20), command = lambda: get_theme_color()).place(anchor = 'center', relx = 0.8, rely = 0.9)        

    #A method to carry out the backend process of changing the password for the user.
    def account_edit_func(self):
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        if self.password_entry.get() == '' or self.confirm_password_entry.get() == '':
            messagebox.showerror("Register Failed", "All fields must be filled out.")
        elif self.password_entry.get() != self.confirm_password_entry.get():
            messagebox.showerror("Register Failed", "Please make sure the passwords are the same.")
        elif not re.match(pattern, self.password_entry.get()):
            messagebox.showerror("Register Failed", "Password is not strong enough. Please include: 8 Characters minimum, A capital letter, A small letter, A number, A symbol.")
        elif re.match(pattern, self.password_entry.get()):
            hashed_password, salt = self.password_hash()
            cursor.execute('''UPDATE User 
                            SET hashed_password = ?, salt = ?
                            WHERE user_id = ?;''', 
                            (hashed_password, salt, self.user.user_id))
            messagebox.showinfo('Password Successfully Set', 'Please login with the new password.')
            conn.commit()
            self.password_entry.set('')
            self.confirm_password_entry.set('')

    #A function to hash the password the user inputted.
    def password_hash(self):
        salt = secrets.token_bytes(16)
        salted_password = self.password_entry.get().encode('utf-8') + salt
        hashed_password = hashlib.sha256(salted_password).hexdigest()
        return hashed_password, salt

    def other(self):
        if self.other_bool.get() == True:
            self.other_texbox.configure(state = 'normal')
            self.problem_combobox.configure(state = 'disabled')
        else:
            self.other_texbox.configure(state = 'disabled')
            self.problem_combobox.configure(state = 'readonly')

    def request_problem(self):
        other_problem = self.other_texbox.get(1.0, "end-1c")
        if self.facility.get() != '' or other_problem != '':
            facility_id_db = cursor.execute('SELECT facility_id FROM Facility WHERE facility_name = ?;', (self.facility.get(),)).fetchall()
            if self.other_bool.get() == False:
                issue_id_db = cursor.execute('SELECT issue_id FROM Issue WHERE issue = ?;', (self.problem.get(),)).fetchall()
                cursor.execute('INSERT INTO IssueRequest (issue_id, facility_id, resolved) VALUES (?, ?, FALSE);', (issue_id_db[0][0], facility_id_db[0][0]))
                conn.commit()
                
            else:
                cursor.execute('INSERT INTO IssueRequest (issue_id, facility_id, other_issue_reason, resolved) VALUES (0, ?, ?, FALSE);', (facility_id_db[0][0], other_problem))
                conn.commit()
            messagebox.showinfo('Request Successful', 'Your issue will be fixed.')
        else:
            messagebox.showerror("Request Failed", "All fields must be filled out.")

#Approval Request
    #A method to display the widgets of the approval request page on the content frame.
    def approval_request(self):
        self.clear_frame()
        
        #Variables
        self.facilities = ('Football', 'Basketball', 'Cricket', 'Multi-Purpose Hall', 'Fitness Suite')
        self.days = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday')
        self.facility = ctk.StringVar()
        self.day = ctk.StringVar()
        self.timing = ctk.StringVar()

        #Widgets
        ctk.CTkLabel(self, text = 'Approval Request', font = ('Impact', 85)).place(anchor = 'center', relx = 0.5, rely = 0.15)
        ctk.CTkLabel(self, text = 'Choose Facility', font = ('Impact', 40)).place(anchor = 'center', relx = 0.3, rely = 0.35)
        ctk.CTkLabel(self, text = 'Pick Day', font = ('Impact', 40)).place(anchor = 'center', relx = 0.3, rely = 0.5)
        ctk.CTkLabel(self, text = 'Pick Timing', font = ('Impact', 40)).place(anchor = 'center', relx = 0.3, rely = 0.65)
        ctk.CTkComboBox(self, state = 'readonly', border_color = 'black', button_color = 'black', width = 250, dropdown_font = ('Impact', 15), variable = self.facility, values = self.facilities).place(anchor = 'center', relx = 0.7, rely = 0.35)
        ctk.CTkComboBox(self, state = 'readonly', border_color = 'black', button_color = 'black', width = 250, dropdown_font = ('Impact', 15), variable = self.day, values = self.days, command = self.display_timings_available).place(anchor = 'center', relx = 0.7, rely = 0.5)
        self.timings_available_combobox = ctk.CTkComboBox(self, state = 'disabled', border_color = 'black', button_color = 'black', width = 250, dropdown_font = ('Impact', 15), variable = self.timing, values = [])
        self.timings_available_combobox.place(anchor = 'center', relx = 0.7, rely = 0.65)
        ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', text = 'Request', font = ('Impact', 20), command = self.request).place(anchor = 'center', relx = 0.5, rely = 0.8)        

    #This method displays the available timings in a combo box.
    def display_timings_available(self, event):
        #An empty array to store the timings available to show the user.
        timings_available = []
        #Retrieves the timings that are available on the database which aren't booked or pending depending on the student's selection: facility and day.
        timings = cursor.execute('''SELECT Timeslot.start_time, Timeslot.end_time 
                                FROM Timeslot, Facility
                                WHERE Facility.facility_id = Timeslot.facility_id 
                                AND Timeslot.day = ?
                                AND Facility.facility_name = ?
                                AND Timeslot.status = 0;''' ,(self.day.get(), self.facility.get())).fetchall()
        #This appends the timings_available array with the timings retrieved from the database whilst also formatting them in a way which is more understandable for the user.
        #Example: 07:40:00 is turned into 07:40
        for slot in timings:
            timings_available.append(f'{slot[0][:-3]} - {slot[1][:-3]}')
        #This allows the combo box to be clickable.
        self.timings_available_combobox.configure(state = 'readonly')
        #This updates the values avaiable in the combo box to the new timings available.
        self.timings_available_combobox.configure(values = timings_available)

    #This method gets the date of the day the user requested since the database requires a date to be stored.
    def get_date(self):
        #Gets the timing in a string format.
        timing_format = self.timing.get()
        #Cycles through every character in the string.
        for index in range(len(timing_format)):
            #If the character is a '-' it uses that as the point in which to change the timing format.
            if timing_format[index] == '-':
                #These lines change the format that was changed for the user's better understanding back into the form the database understands.
                #Example: 07:40 is turned into 07:40:00
                self.start_time = f'{timing_format[:index - 1].strip()}:00'
                self.end_time = f'{timing_format[index + 1:].strip()}:00'
        #Gets the day in a string format.
        day = self.day.get()
        #Gets todays date as an object
        today = datetime.today()
        Day_num = {'Monday' : 0, 'Tuesday' : 1, 'Wednesday' : 2, 'Thursday' : 3, 'Friday' : 4}
        #These lines retrieve how many days remain until the day of the booking and calculates the date based on today's date.
        days_delta = (Day_num[day] - today.weekday()) % 7
        self.date = (today + timedelta(days=days_delta)).strftime('%Y-%m-%d')

    #This method sends the request on the database for the teacher or admin to view later on.
    def request(self):
        #The get_date method is called.
        self.get_date()
        #This retrieves the facility id of the corresponding facility picked by the user.
        facility_id_db = cursor.execute('SELECT facility_id FROM Facility WHERE facility_name = ?', (self.facility.get(), )).fetchall()
        #This retrieves the timeslot the user has requested to book.
        self.timeslot_id_db = cursor.execute('SELECT timeslot_id FROM Timeslot WHERE day = ? AND facility_id = ? AND start_time = ? AND end_time = ?', (self.day.get(), facility_id_db[0][0], self.start_time, self.end_time)).fetchall()
        #This creates the request on the database with setting the status to NULL which means pending.
        cursor.execute('INSERT INTO Booking (facility_id, user_id, timeslot_id, booking_date) VALUES (?, ?, ?, ?)', (facility_id_db[0][0], self.user.user_id, self.timeslot_id_db[0][0], self.date))
        #This updates the status of the time slot to NULL also to indicate a pending request.
        cursor.execute('UPDATE Timeslot SET status = NULL WHERE timeslot_id = ?', (self.timeslot_id_db[0][0],))
        conn.commit()
        #These lines reset the page for a new request.
        self.day.set('')
        self.timing.set('')
        self.timings_available_combobox.configure(state = 'disabled')
        #This shows an appropriate message to the user about the info of their booking.
        messagebox.showinfo('Request Successful', f'Requested {self.facility.get()} from {self.start_time} to {self.end_time} on {self.day.get()} {self.date}')

#Card Tap in
    #A method which shows a combo box of facilities to tap in to and a button to do so.
    def card_tap_in_page(self):
        self.clear_frame()
        self.facility_choice = ctk.StringVar()
        self.facilities = ('Football', 'Basketball', 'Cricket', 'Multi-Purpose Hall', 'Fitness Suite')
        ctk.CTkComboBox(self, values = self.facilities, variable = self.facility_choice).place(anchor = 'center', relx = 0.5, rely = 0.2)
        ctk.CTkButton(self, text = 'Tap In', command = self.card_tap_in_func).place(anchor = 'center', relx = 0.5, rely = 0.4) 

    #A method which carries out the backend process of the card tap in into a facility.
    def card_tap_in_func(self):
        #These lines get the current date and time and formats them into a string to be compared later.
        current_date_time = datetime.now()
        self.current_time = current_date_time.strftime('%H:%M:%S')
        self.current_date = current_date_time.strftime('%Y-%m-%d')
        #This returns if the facility requires a booking or not.
        self.facility_booking_required = cursor.execute('''SELECT facility_id, booking_required 
                                                FROM Facility
                                                WHERE facility_name = ?''', (self.facility_choice.get(),)).fetchall()
        #Checks if the user is a student, teacher or admin.
        if self.user.user_id[0] == 'A':
            self.access_granted()
        elif self.user.user_id[0] == 'T':
            #Checks whether the teacher is entitled to the facility they are trying to tap in to or if the facility even requires a booking.
            if self.user.facility_id == self.facility_booking_required[0][0] or self.facility_booking_required[0][1] == 0:
                self.access_granted()
            else:
                self.access_denied()
        elif self.user.user_id[0] == 'S':
            #Checks if the facility requires a booking to access.
            if self.facility_booking_required[0][1] == 1:
                #Retrives the user's booking of the specific facility they are trying to access at the specific time they're trying to access and whether they have a booking or not.
                booking_date_info = cursor.execute('''SELECT start_time, end_time, booking_date
                                                    FROM User, Booking, Timeslot
                                                    WHERE User.user_id = Booking.user_id
                                                    AND User.user_id = ?
                                                    AND Booking.facility_id = ?
                                                    AND Timeslot.timeslot_id = Booking.timeslot_id
                                                    AND Timeslot.status = 1
                                                    AND Timeslot.start_time <= ?
                                                    AND Timeslot.end_time >= ?
                                                    AND Booking.booking_date = ?''', 
                                                    (self.user.user_id, self.facility_booking_required[0][0], self.current_time, self.current_time, self.current_date)).fetchall()
                #Checks whether a booking is returned or not and carries out the respective command.
                if booking_date_info != []:
                    self.access_granted()
                else:
                    self.access_denied()
            else:
                self.access_granted()
        conn.commit()

    #A method which carries out the backend process of swipe being granted into the facility.
    def access_granted(self):
        #Inserts info about the current swipe that has just occurred into the database with the access_accepted value as True.
        cursor.execute('''INSERT INTO Swipe (card_id, facility_id, date, time, access_accepted)
                                        VALUES (?, ?, ?, ?, TRUE)''',
                                        (self.card.card_id, self.facility_booking_required[0][0], self.current_date, self.current_time))
        #Shows an appropriate message to the user that their access has been granted.
        messagebox.showinfo('', 'Access Granted')

    #A method which carries out the backend process of swipe being denied into the facility.
    def access_denied(self):
        cursor.execute('''INSERT INTO Swipe (card_id, facility_id, date, time, access_accepted)
                        VALUES (?, ?, ?, ?, FALSE)''',
                        (self.card.card_id, self.facility_booking_required[0][0], self.current_date, self.current_time))
        messagebox.showerror('', 'Access Denied')

#Approval Management
    #A method which checks whether a student, teacher or admin is accessing the approvals page and shows them page for their appropriate role.
    def approval_management(self):
        self.clear_frame()
        #Checks whether a student, teacher or admin is logged in and using the system.
        if self.user.user_id[0] == 'A' or self.user.user_id[0] == 'T':
            #Checks whether it's a teacher or admin accessing this page.
            if self.user.user_id[0] == 'A':
                #Gets the requests from all facilites.
                bookings = cursor.execute('''SELECT Booking.booking_number, Facility.facility_name, Timeslot.start_time, Timeslot.end_time, Timeslot.day, Booking.booking_date, Booking.approved, Booking.timeslot_id, User.first_name, User.last_name, User.class_grade, User.user_id
                                            FROM Facility, Timeslot, Booking, User
                                            WHERE Booking.facility_id = Facility.facility_id
                                            AND Booking.approved IS NULL
                                            AND Booking.timeslot_id = Timeslot.timeslot_id
                                            AND User.user_id = Booking.user_id;''').fetchall()
            elif self.user.user_id[0] == 'T':
                #Gets the requests from the teacher's specific facility.
                bookings = cursor.execute('''SELECT Booking.booking_number, Facility.facility_name, Timeslot.start_time, Timeslot.end_time, Timeslot.day, Booking.booking_date, Booking.approved, Booking.timeslot_id, User.first_name, User.last_name, User.class_grade, User.user_id
                                            FROM Facility, Timeslot, Booking, User
                                            WHERE Booking.facility_id = Facility.facility_id
                                            AND Booking.approved IS NULL
                                            AND Booking.facility_id = ?
                                            AND Booking.timeslot_id = Timeslot.timeslot_id
                                            AND User.user_id = Booking.user_id;''', (self.user.facility,)).fetchall()
            #Checks whether there are requests and shows an appropriate message if there aren't.
            if bookings != []:
                #A scrollable frame widget which allows for multiple requests to be shown and once on the screen.
                incoming_approval_object_frame = ctk.CTkScrollableFrame(self, width = 620, height = 342, corner_radius = 0, border_color = 'black', border_width = 2) #fg_color = '#F0F0F0')
                incoming_approval_object_frame.place(anchor = 'n', relx = 0.5, rely = 0.36)
                #An array to carry all incoming requests objects that will be created.
                incoming_approval_objects = []
                #Goes through every request that had been retrieved from the database.
                for booking in bookings:
                    #Creates an object using the IncomingApprovalSegment class.
                    approval_object = IncomingApprovalSegment(incoming_approval_object_frame, incoming_approval_objects, booking, self.card)
                    #Appends the object created to the previously created array.
                    incoming_approval_objects.append(approval_object)
                #Widgets
                title_font = ctk.CTkFont(family = 'Impact', size = 18, underline = True)
                ctk.CTkLabel(self, text = 'Incoming Approvals', font = ('Impact', 70)).place(anchor = 'center', relx = 0.5, rely = 0.15)
                ctk.CTkLabel(self, text = 'User ID', font = title_font).place(anchor = 'center', relx = 0.085, rely = 0.33)
                ctk.CTkLabel(self, text = 'Facility', font = title_font).place(anchor = 'center', relx = 0.22, rely = 0.33)
                ctk.CTkLabel(self, text = 'Start Time', font = title_font).place(anchor = 'center', relx = 0.36, rely = 0.33)
                ctk.CTkLabel(self, text = 'End Time', font = title_font).place(anchor = 'center', relx = 0.5, rely = 0.33)
                ctk.CTkLabel(self, text = 'Day', font = title_font).place(anchor = 'center', relx = 0.64, rely = 0.33)
                ctk.CTkLabel(self, text = 'Date', font = title_font).place(anchor = 'center', relx = 0.77, rely = 0.33)
            else:
                ctk.CTkLabel(self, text = 'There are no incoming requests', font = ('Impact', 45)).place(anchor = 'center', relx = 0.5, rely = 0.5)   
        else:
            #Gets the requests the student themselves have sent.
            bookings = cursor.execute('''SELECT Booking.booking_number, Facility.facility_name, Timeslot.start_time, Timeslot.end_time, Timeslot.day, Booking.booking_date, Booking.approved, Booking.timeslot_id 
                                        FROM Facility, Timeslot, Booking 
                                        WHERE Facility.facility_id = Booking.facility_id
                                            AND Timeslot.timeslot_id = Booking.timeslot_id
                                            AND Booking.user_id = ?;''', (self.user.user_id,)).fetchall()
            #The same format repeats except for some factors.
            if bookings != []:
                outgoing_approval_object_frame = ctk.CTkScrollableFrame(self, width = 620, height = 342, corner_radius = 0, border_color = 'black', border_width = 2) #fg_color = '#F0F0F0')
                outgoing_approval_object_frame.place(anchor = 'n', relx = 0.5, rely = 0.36)
                outgoing_approval_objects = []
                for booking in bookings:
                    #Converts status on the database to one the user can understand.
                    if booking[6] == None: status = 'Pending'
                    elif booking[6] == 1: status = 'Approved'
                    else: status = 'Declined'
                    #An outgoing approval object is created rather than an incoming one.
                    approval_object = OutgoingApprovalSegment(outgoing_approval_object_frame, booking, status, outgoing_approval_objects)
                    outgoing_approval_objects.append(approval_object)
                #Widgets
                title_font = ctk.CTkFont(family = 'Impact', size = 18, underline = True)
                ctk.CTkLabel(self, text = 'Sent Approvals', font = ('Impact', 90)).place(anchor = 'center', relx = 0.5, rely = 0.15)
                ctk.CTkLabel(self, text = 'Facility', font = title_font).place(anchor = 'center', relx = 0.085, rely = 0.33)
                ctk.CTkLabel(self, text = 'Start Time', font = title_font).place(anchor = 'center', relx = 0.24, rely = 0.33)
                ctk.CTkLabel(self, text = 'End Time', font = title_font).place(anchor = 'center', relx = 0.39, rely = 0.33)
                ctk.CTkLabel(self, text = 'Day', font = title_font).place(anchor = 'center', relx = 0.545, rely = 0.33)
                ctk.CTkLabel(self, text = 'Date', font = title_font).place(anchor = 'center', relx = 0.695, rely = 0.33)
                ctk.CTkLabel(self, text = 'Status', font = title_font).place(anchor = 'center', relx = 0.855, rely = 0.33)
            else:
                ctk.CTkLabel(self, text = 'You have no requests sent', font = ('Impact', 50)).place(anchor = 'center', relx = 0.5, rely = 0.5)

#Schedule Viewer
    #A method which displays the accepted bookings.
    def schedule_viewer(self):
        self.clear_frame()
        #Checks whether a teacher or admin is using the accessing the page.
        if self.user.user_id[0] == 'A':
            #Retrives all records from the booking table of which are approved.
            bookings = cursor.execute('''SELECT Booking.booking_number, Facility.facility_name, Timeslot.start_time, Timeslot.end_time, Timeslot.day, Booking.booking_date, Booking.approved, Booking.timeslot_id, User.first_name, User.last_name, User.class_grade, User.user_id
                                        FROM Facility, Timeslot, Booking, User
                                        WHERE Booking.facility_id = Facility.facility_id
                                        AND Booking.approved = TRUE
                                        AND Booking.timeslot_id = Timeslot.timeslot_id
                                        AND User.user_id = Booking.user_id;''').fetchall()
        elif self.user.user_id[0] == 'T':
            #Retrives all records from the booking table of which are approved and the facility of which the teacher is entitled to.
            bookings = cursor.execute('''SELECT Booking.booking_number, Facility.facility_name, Timeslot.start_time, Timeslot.end_time, Timeslot.day, Booking.booking_date, Booking.approved, Booking.timeslot_id, User.first_name, User.last_name, User.class_grade, User.user_id
                                        FROM Facility, Timeslot, Booking, User
                                        WHERE Booking.facility_id = Facility.facility_id
                                        AND Booking.approved = TRUE
                                        AND Booking.timeslot_id = Timeslot.timeslot_id
                                        AND User.user_id = Booking.user_id
                                        AND Facility.facility_id = ?;''', (self.user.facility_id,)).fetchall()
        #Checks if there are any records and shows the appropriate widgets on the screen.
        if bookings != []:
            #A scrollable frame widget which allows for multiple bookings to be shown at once on the screen.
            bookings_frame = ctk.CTkScrollableFrame(self, width = 620, height = 342, corner_radius = 0, border_color = 'black', border_width = 2) #fg_color = '#F0F0F0')
            bookings_frame.place(anchor = 'n', relx = 0.5, rely = 0.36)
            #An array to carry all booking objects that will be created.
            booking_objects = []
            #Goes through every booking that has been retrieved from the database.
            for booking in bookings:
                #Creates an object using the ScheduledBookingSegment class.
                approval_object = ScheduledBookingSegment(bookings_frame, booking_objects, booking, self.card, self.user)
                #Appends the object created to the previously created array.                
                booking_objects.append(approval_object)
            #Widgets
            title_font = ctk.CTkFont(family = 'Impact', size = 18, underline = True)
            ctk.CTkLabel(self, text = 'Scheduled Bookings', font = ('Impact', 75)).place(anchor = 'center', relx = 0.5, rely = 0.15)
            ctk.CTkLabel(self, text = 'User ID', font = title_font).place(anchor = 'center', relx = 0.085, rely = 0.33)
            ctk.CTkLabel(self, text = 'Facility', font = title_font).place(anchor = 'center', relx = 0.24, rely = 0.33)
            ctk.CTkLabel(self, text = 'Start Time', font = title_font).place(anchor = 'center', relx = 0.39, rely = 0.33)
            ctk.CTkLabel(self, text = 'End Time', font = title_font).place(anchor = 'center', relx = 0.545, rely = 0.33)
            ctk.CTkLabel(self, text = 'Day', font = title_font).place(anchor = 'center', relx = 0.695, rely = 0.33)
            ctk.CTkLabel(self, text = 'Date', font = title_font).place(anchor = 'center', relx = 0.855, rely = 0.33)
        else:
            ctk.CTkLabel(self, text = 'Empty Schedule', font = ('Impact', 50)).place(anchor = 'center', relx = 0.5, rely = 0.5)

#Record Viewer
    #A method which displays the visual part of the records page.
    def all_records_page(self):
        self.clear_frame()
        #Variables
        self.selection_occupation = ctk.StringVar()
        self.selection_facility = ctk.StringVar()
        self.selection_occupation.set('All')
        self.selection_facility.set('All')
        self.occupations = ('All', 'Teachers', 'Students')
        self.facilities = ('All', 'Football', 'Sixth Form Room', 'Basketball', 'Cricket', 'Multi-Purpose Hall', 'Fitness Suite')
        #Widgets
        heading_font = ctk.CTkFont(family = 'Impact', size = 90, underline = True)
        ctk.CTkLabel(self, text = 'Records', font = heading_font).place(anchor = 'center', relx = 0.34, rely = 0.18)
        ctk.CTkComboBox(self, variable = self.selection_occupation, values = self.occupations, state = 'readonly', border_color = 'black', button_color = 'black', dropdown_font = ('Impact', 15)).place(anchor = 'center', relx = 0.8, rely = 0.08)
        self.facility_combobox = ctk.CTkComboBox(self, variable = self.selection_facility, values = self.facilities, state = 'readonly', border_color = 'black', button_color = 'black', dropdown_font = ('Impact', 15))
        self.facility_combobox.place(anchor = 'center', relx = 0.8, rely = 0.18)
        ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', text = 'Search', font = ('Impact', 20), command = self.all_records_func).place(anchor = 'center', relx = 0.8, rely = 0.28)
        self.all_records_func()

    #A method to carry out the backend processes of retrieving values from the database to show them to the user in a presentable way.
    def all_records_func(self):
        #Checks whether a filter is applied or not.
        if self.selection_occupation.get() == 'All':
                self.facility_combobox.configure(state = 'disabled')
                #Retrieves all the teacher records. 
                teacher_records = cursor.execute('''SELECT User.user_id, facility_name, first_name, last_name, card_id
                                        FROM User, Card, Facility
                                        WHERE User.user_id = Card.user_id
                                        AND User.user_id <> 'A'
                                        AND Facility.facility_id = User.facility_id;''').fetchall()
                #Retrieves all the student records.
                student_records = cursor.execute('''SELECT User.user_id, class_grade, first_name, last_name, card_id
                                        FROM User, Card
                                        WHERE User.user_id = Card.user_id
                                        AND User.user_id <> 'A'
                                        AND User.facility_id IS NULL''').fetchall()
                #Combines them into all records.
                records = teacher_records + student_records
        elif self.selection_occupation.get() == 'Teachers':
            self.facility_combobox.configure(state = 'readonly')    
            if self.selection_facility.get() == 'All':
                #Retrieves all teachers.
                records = cursor.execute('''SELECT User.user_id, facility_name, first_name, last_name, card_id
                                        FROM User, Card, Facility
                                        WHERE User.user_id = Card.user_id
                                        AND User.user_id <> 'A'
                                        AND Facility.facility_id = User.facility_id;''').fetchall()
            else:
                #Retrieves all teachers responsible for a specific facility.
                records = cursor.execute('''SELECT User.user_id, facility_name, first_name, last_name, card_id
                                        FROM User, Card, Facility
                                        WHERE User.user_id = Card.user_id
                                        AND User.user_id <> 'A'
                                        AND Facility.facility_id = User.facility_id
                                        AND Facility.facility_name = ?;''', (self.selection_facility.get(),)).fetchall()
        elif self.selection_occupation.get() == 'Students':
            self.facility_combobox.configure(state = 'disabled')
            #Retrieves all students.  
            records = cursor.execute('''SELECT User.user_id, class_grade, first_name, last_name, card_id
                                        FROM User, Card
                                        WHERE User.user_id = Card.user_id
                                        AND User.user_id <> 'A'
                                        AND User.facility_id IS NULL''').fetchall()
        #Checks whether there are any records and shows the appropriate widgets.
        if records != []:
            record_objects = []
            records_frame = ctk.CTkScrollableFrame(self, width = 620, height = 330, corner_radius = 0, border_color = 'black', border_width = 2)
            records_frame.place(anchor = 'n', relx = 0.5, rely = 0.382)
            for record in records:
                record_obj = Records(records_frame, self.user, record, record_objects)
                record_objects.append(record_obj)    
            #Widgets
            title_font = ctk.CTkFont(family = 'Impact', size = 18, underline = True)
            ctk.CTkLabel(self, text = 'User ID', font = title_font).place(anchor = 'center', relx = 0.15, rely = 0.35)
            ctk.CTkLabel(self, text = 'Card ID', font = title_font).place(anchor = 'center', relx = 0.77, rely = 0.35)
            ctk.CTkLabel(self, text = 'Class/Facility', font = title_font).place(anchor = 'center', relx = 0.3, rely = 0.35)
            ctk.CTkLabel(self, text = 'First Name', font = title_font).place(anchor = 'center', relx = 0.465, rely = 0.35)
            ctk.CTkLabel(self, text = 'Last Name', font = title_font).place(anchor = 'center', relx = 0.61, rely = 0.35)
        else:
            ctk.CTkLabel(self, text = 'There are no records', font = ('Impact', 50)).place(anchor = 'center', relx = 0.5, rely = 0.5)

#Analytics
    #A method which displays two options to choose from to the user.
    def analytics_page(self):
        self.clear_frame()
        ctk.CTkLabel(self, text = 'Analytics', font = ('Impact', 75)).place(anchor = 'center', relx = 0.5, rely = 0.15)
        ctk.CTkButton(self, text = 'Bookings per facility', width = 200, height = 200, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = self.bookings_per_facility_page).place(anchor = 'e', relx = 0.45, rely = 0.5)
        ctk.CTkButton(self, text = 'Booking trends\nover time', width = 200, height = 200, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = self.booking_trends_over_time_page).place(anchor = 'w', relx = 0.55, rely = 0.5)

    #A method to show the filter options the user can choose from to display a cofiguration of a graph.
    def bookings_per_facility_page(self):
        self.clear_frame()
        #Variables
        self.options = ('All-Time', 'Day', 'Date')
        self.option = ctk.StringVar()
        self.option.set('All-Time')
        self.facilities = ('All', 'Football', 'Basketball', 'Cricket', 'Multi-Purpose Hall', 'Fitness Suite')
        self.facility = ctk.StringVar()
        self.facility.set('All')
        self.statuses = ('All', 'Approved', 'Pending', 'Declined')
        self.statuses_dict = {'Approved': 1, 'Pending': None, 'Declined': 0}
        self.status = ctk.StringVar()
        self.status.set('All')
        self.days = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday')
        self.day = ctk.StringVar()
        #Widgets
        ctk.CTkComboBox(self, variable = self.option, values = self.options, state = 'readonly', border_color = 'black', button_color = 'black', dropdown_font = ('Impact', 15), command = self.options_choice_bookings_per_facility_page).place(anchor = 'center', relx = 0.5, rely = 0.1)
        ctk.CTkComboBox(self, variable = self.facility, values = self.facilities, state = 'readonly', border_color = 'black', button_color = 'black', dropdown_font = ('Impact', 15)).place(anchor = 'center', relx = 0.5, rely = 0.2)
        ctk.CTkComboBox(self, variable = self.status, values = self.statuses, state = 'readonly', border_color = 'black', button_color = 'black', dropdown_font = ('Impact', 15)).place(anchor = 'center', relx = 0.5, rely = 0.3)
        self.days_combobox = ctk.CTkComboBox(self, variable = self.day, values = self.days, state = 'disabled', border_color = 'black', button_color = 'black', dropdown_font = ('Impact', 15))
        self.days_combobox.place(anchor = 'center', relx = 0.5, rely = 0.4)
        self.start_date_button = ctk.CTkButton(self, state = 'disabled', hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text = "Select Start Date", text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = self.get_start_date)
        self.start_date_button.place(anchor = 'center', relx = 0.5, rely = 0.5)
        self.end_date_button = ctk.CTkButton(self, state = 'disabled', hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text = "Select End Date", text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = self.get_end_date)
        self.end_date_button.place(anchor = 'center', relx = 0.5, rely = 0.6)
        ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text = 'Generate', text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = self.bookings_per_facility_func).place(anchor = 'center', relx = 0.5, rely = 0.7)

    #A method to activate and deactivate certain combo boxes depending on the user's selection.    
    def options_choice_bookings_per_facility_page(self, event):
        #Checks if the combo box is set to day, it then disables the button to choose the date and activates the day combo box and vice versa.
        if event == 'Day':
            self.days_combobox.configure(state = 'readonly')
            self.start_date_button.configure(state = 'disabled')
            self.end_date_button.configure(state = 'disabled')
        elif event == 'Date':
            self.days_combobox.configure(state = 'disabled')
            self.start_date_button.configure(state = 'normal')
            self.end_date_button.configure(state = 'normal')

    #This creates a window pop up to show a calendar where the user can choose the start date.
    def get_start_date(self):
        #Creates the calendar
        calender = Querybox()
        #Shows the user the calendar and retrieves the value selected.
        self.start_date = calender.get_date(title = 'Calender', bootstyle = 'dark')
        #Changes the button to the start date chosen.
        self.start_date_button.configure(text = self.start_date)

    #This creates a window pop up to show a calendar where the user can choose the end date.
    def get_end_date(self):
        #Creates the calendar
        calender = Querybox()
        #Shows the user the calendar and retrieves the value selected.
        self.end_date = calender.get_date(title = 'Calender', bootstyle = 'dark')
        #Changes the button to the start date chosen.
        self.end_date_button.configure(text = self.end_date)

    #A method to carry out the backend process of retrieving the specific bookings from the specific configuration the user has choosed from.
    def bookings_per_facility_func(self):
        #Checks the specific filter configuation of the user and carries out the specific sql command of counting the bookings which are retrieved of that configuartion.
        if self.option.get() == 'All-Time':
            if self.facility.get() == 'All':
                if self.status.get() == 'All':
                    #(All time)(All facilities)(All statuses)
                    result = cursor.execute('''SELECT facility_name, COUNT(*) as booking_count
                                            FROM Booking, Facility
                                            WHERE Booking.facility_id = Facility.facility_id
                                            GROUP BY facility_name
                                            ORDER BY booking_count DESC''').fetchall()
                    title = 'Total Booking Counts Per Facility'
                else:
                    #(All time)(All facilities)(specific status)
                    result = cursor.execute('''SELECT facility_name, COUNT(*) as booking_count
                                            FROM Booking, Facility
                                            WHERE Booking.facility_id = Facility.facility_id
                                            AND Booking.approved = ?
                                            GROUP BY facility_name
                                            ORDER BY booking_count DESC''', (self.statuses[self.status.get()],)).fetchall()
                    title = f'Total Booking Counts Per Facility ({self.statuses_dict[self.status.get()]})'
            else:
                if self.status.get() == 'All':
                    #(All time)(Specific Facility)(All statuses)
                    result = cursor.execute('''SELECT facility_name, COUNT(*) as booking_count
                                            FROM Booking, Facility
                                            WHERE Booking.facility_id = Facility.facility_id
                                            AND Facility.facility_name = ?
                                            GROUP BY facility_name
                                            ORDER BY booking_count DESC''', (self.facility.get(),)).fetchall()
                    title = f'Total Booking Counts Per Facility ({self.facility.get()})'
                else:
                    #(All time)(Specific Facility)(Specifc status)
                    result = cursor.execute('''SELECT facility_name, COUNT(*) as booking_count
                                            FROM Booking, Facility
                                            WHERE Booking.facility_id = Facility.facility_id
                                            AND Facility.facility_name = ?
                                            AND Booking.approved = ?
                                            GROUP BY facility_name
                                            ORDER BY booking_count DESC''', 
                                            (self.facility.get(), self.statuses_dict[self.status.get()])).fetchall()
                    title = f'Total Booking Counts Per Facility ({self.facility.get()})({self.status.get()})'
        elif self.option.get() == 'Day':
            if self.facility.get() == 'All':
                if self.status.get() == 'All':
                    #(Specific day)(All Facilities)(All statuses)
                    result = cursor.execute('''SELECT facility_name, COUNT(*) as booking_count
                                            FROM Booking, Facility, Timeslot
                                            WHERE Booking.facility_id = Facility.facility_id
                                            AND Booking.timeslot_id = Timeslot.timeslot_id
                                            AND Timeslot.day = ?
                                            GROUP BY facility_name
                                            ORDER BY booking_count DESC''', (self.day.get(),)).fetchall()
                    title = f'Total Booking Counts Per Facility ({self.day.get()})'
                else:
                    #(Specific day)(All Facilities)(Specific Status)
                    result = cursor.execute('''SELECT facility_name, COUNT(*) as booking_count
                                            FROM Booking, Facility, Timeslot
                                            WHERE Booking.facility_id = Facility.facility_id
                                            AND Booking.timeslot_id = Timeslot.timeslot_id
                                            AND Timeslot.day = ?
                                            AND Booking.approved = ?
                                            GROUP BY facility_name
                                            ORDER BY booking_count DESC''',
                                            (self.day.get(), self.statuses_dict[self.status.get()])).fetchall()
                    title = f'Total Booking Counts Per Facility ({self.day.get()})({self.status.get()})'
            else:
                if self.status.get() == 'All':
                    #(Specific day)(Specific Facility)(All Statuses)
                    result = cursor.execute('''SELECT facility_name, COUNT(*) as booking_count
                                            FROM Booking, Facility, Timeslot
                                            WHERE Booking.facility_id = Facility.facility_id
                                            AND Booking.timeslot_id = Timeslot.timeslot_id
                                            AND Timeslot.day = ?
                                            AND Facility.facility_name = ?
                                            GROUP BY facility_name
                                            ORDER BY booking_count DESC''', (self.day.get(), self.facility.get())).fetchall()
                    title = f'Total Booking Counts Per Facility ({self.day.get()})({self.facility.get()})'
                else:
                    #(Specific day)(Specific Facility)(Specific Status)
                    result = cursor.execute('''SELECT facility_name, COUNT(*) as booking_count
                                            FROM Booking, Facility, Timeslot
                                            WHERE Booking.facility_id = Facility.facility_id
                                            AND Booking.timeslot_id = Timeslot.timeslot_id
                                            AND Timeslot.day = ?
                                            AND Facility.facility_name = ?
                                            AND Booking.approved = ?
                                            GROUP BY facility_name
                                            ORDER BY booking_count DESC''', (self.day.get(), self.facility.get(), self.statuses_dict[self.status.get()])).fetchall()
                    title = f'Total Booking Counts Per Facility ({self.day.get()})({self.facility.get()})({self.status.get()})'
        else:
            if self.facility.get() == 'All':
                if self.status.get() == 'All':
                    #(Specific date range)(All facilities)(All statuses)
                    result = cursor.execute('''SELECT facility_name, COUNT(*) as booking_count
                                            FROM Booking, Facility
                                            WHERE Booking.facility_id = Facility.facility_id
                                            AND booking_date >= ?
                                            AND booking_date <= ?
                                            GROUP BY facility_name
                                            ORDER BY booking_count DESC''', (self.start_date, self.end_date)).fetchall()
                    title = f'Total Booking Counts Per Facility ({self.start_date}) to ({self.end_date})'
                else:
                    #(Specific date range)(All facilities)(Specific Status)
                    result = cursor.execute('''SELECT facility_name, COUNT(*) as booking_count
                                            FROM Booking, Facility
                                            WHERE Booking.facility_id = Facility.facility_id
                                            AND booking_date >= ?
                                            AND booking_date <= ?
                                            AND Booking.approved = ?
                                            GROUP BY facility_name
                                            ORDER BY booking_count DESC''',
                                            (self.start_date, self.end_date, self.statuses_dict[self.status.get()])).fetchall()
                    title = f'Total Booking Counts Per Facility ({self.start_date}) to ({self.end_date})({self.status.get()})'
            else:
                if self.status.get() == 'All':
                    #(Specific date range)(Specific Facility)(All Statuses)
                    result = cursor.execute('''SELECT facility_name, COUNT(*) as booking_count
                                            FROM Booking, Facility
                                            WHERE Booking.facility_id = Facility.facility_id
                                            AND booking_date >= ?
                                            AND booking_date <= ?
                                            AND Facility.facility_name = ?
                                            GROUP BY facility_name
                                            ORDER BY booking_count DESC''', (self.start_date, self.end_date, self.facility.get())).fetchall()
                    title = f'Total Booking Counts Per Facility ({self.start_date}) to ({self.end_date})({self.facility.get()})'
                else:
                    #(Specific date range)(Specific Facility)(Specific Status)
                    result = cursor.execute('''SELECT facility_name, COUNT(*) as booking_count
                                            FROM Booking, Facility
                                            WHERE Booking.facility_id = Facility.facility_id
                                            AND booking_date >= ?
                                            AND booking_date <= ?
                                            AND Facility.facility_name = ?
                                            AND Booking.approved = ?
                                            GROUP BY facility_name
                                            ORDER BY booking_count DESC''', (self.start_date, self.end_date, self.facility.get(), self.statuses_dict[self.status.get()])).fetchall()
                    title = f'Total Booking Counts Per Facility ({self.start_date}) to ({self.end_date})({self.facility.get()})({self.status.get()})'
        #Checks if there are any bookings for that configuration.
        if result != []:
            #Seperates the specific facility and count for each.
            facilities, counts = zip(*result)
            #Creates a matplotlib figure
            plt.figure(figsize = (10, 6), edgecolor = 'black')
            #Creates a bar graph with the specific values with the facilities being on the x axis and the counts on the y axis.
            plt.bar(facilities, counts, color = theme_color, edgecolor = 'black')
            #Gives the graph a title of th specific configuration.
            plt.title(title)
            #Gives the axis their respective labels.
            plt.xlabel('Facility')
            plt.ylabel('Booking Count')
            plt.grid(axis='y')
            #This creates tooltips for each of the bars on the graph to show their actual values.
            mplcursors.cursor(hover=True).connect("add", lambda sel: sel.annotation.set_text(f'Value: {counts[sel.target.index]}'))
            #This shows the graph of that specific configuration on a pop up window.
            plt.show()
        else:
            #Shows an appropriate message if there are bo bookings for this configuration.
            messagebox.showinfo('No Results', 'There are no bookings for this configuration.')

    #A method to show the filter options the user can choose from to display a configuration of a graph.
    def booking_trends_over_time_page(self):
        #Variables
        self.clear_frame()
        self.options = ('All-Time', 'Date')
        self.option = ctk.StringVar()
        self.option.set('All-Time')
        self.facilities = ('All', 'Football', 'Basketball', 'Cricket', 'Multi-Purpose Hall', 'Fitness Suite')
        self.facility = ctk.StringVar()
        self.facility.set('All')
        #Widgets
        ctk.CTkComboBox(self, variable = self.option, values = self.options, state = 'readonly', border_color = 'black', button_color = 'black', dropdown_font = ('Impact', 15), command = self.options_choice_booking_trends_over_time_page).place(anchor = 'center', relx = 0.5, rely = 0.1)
        ctk.CTkComboBox(self, variable = self.facility, values = self.facilities, state = 'readonly', border_color = 'black', button_color = 'black', dropdown_font = ('Impact', 15)).place(anchor = 'center', relx = 0.5, rely = 0.2)
        self.start_date_button = ctk.CTkButton(self, state = 'disabled', hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text = "Select Start Date", text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = self.get_start_date)
        self.start_date_button.place(anchor = 'center', relx = 0.5, rely = 0.3)
        self.end_date_button = ctk.CTkButton(self, state = 'disabled', hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text = "Select End Date", text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = self.get_end_date)
        self.end_date_button.place(anchor = 'center', relx = 0.5, rely = 0.4)
        ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text = 'Generate', text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = self.booking_trends_over_time_func).place(anchor = 'center', relx = 0.5, rely = 0.5)

    #A method to activate and deactivate certain combo boxes depending on the user's selection.    
    def options_choice_booking_trends_over_time_page(self, event):
            if event == 'All-Time':
                self.start_date_button.configure(state = 'disabled')
                self.end_date_button.configure(state = 'disabled')
            else:
                self.start_date_button.configure(state = 'normal')
                self.end_date_button.configure(state = 'normal')

    #A method to carry out the backend process of retrieving the specific bookings from the specific configuration the user has choosed from.
    def booking_trends_over_time_func(self):
        #Checks the specific filter configuation of the user and carries out the specific sql command of counting the bookings which are retrieved of that configuartion.
        if self.option.get() == 'All-Time':
            if self.facility.get() == 'All':
                #(All time)(All facilities)
                result = cursor.execute('''SELECT booking_date, COUNT(*) as booking_count
                                        FROM Booking
                                        GROUP BY booking_date
                                        ORDER BY booking_date;''').fetchall()
            else:
                #(All time)(Specific facility)
                result = cursor.execute('''SELECT booking_date, COUNT(*) as booking_count
                                        FROM Booking, Facility
                                        WHERE Booking.facility_id = Facility.facility_id
                                        AND facility_name = ?
                                        GROUP BY booking_date
                                        ORDER BY booking_date;''', (self.facility.get(),)).fetchall()    
        else:
            if self.facility.get() == 'All':
                #(Specific date range)(All facilities)
                result = cursor.execute('''SELECT booking_date, COUNT(*) as booking_count
                                        FROM Booking
                                        WHERE booking_date >= ?
                                        AND booking_date <= ?
                                        GROUP BY booking_date
                                        ORDER BY booking_date;''', (self.start_date, self.end_date)).fetchall()   
            else:#(Specific date range)(Specific facility)
                result = cursor.execute('''SELECT booking_date, COUNT(*) as booking_count
                                        FROM Booking
                                        WHERE Booking.facility_id = Facility.facility_id
                                        AND booking_date >= ?
                                        AND booking_date <= ?
                                        AND Facility.facility_name = ?
                                        GROUP BY booking_date
                                        ORDER BY booking_date;''', (self.start_date, self.end_date, self.facility.get())).fetchall()            
        #Checks if there are any bookings for that configuration.
        if result != []:
            # Separate dates and counts
            dates, counts = zip(*result)
            # Convert date strings to datetime objects
            dates = [datetime.strptime(date, '%Y-%m-%d') for date in dates]
            # Plot the data
            plt.figure(figsize=(10, 6))
            plt.plot_date(dates, counts, '-', color = theme_color)
            plt.title('Booking Trends Over Time')
            plt.xlabel('Date')
            plt.ylabel('Booking Count')
            # Formatting the x-axis to show dates nicely
            plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.gcf().autofmt_xdate()
            plt.show()
        else:
            #Shows an appropriate message if there are bo bookings for this configuration.
            messagebox.showinfo('No Results', 'There are no bookings of this configuration.')

#Add Records
    #A method to show the admin empty entry boxed for them to input a new user into the system.
    def add_records_page(self):
        self.clear_frame()
        #Variables
        self.user_id = ctk.StringVar()
        self.first_name = ctk.StringVar()
        self.last_name = ctk.StringVar()
        self.class_facility = ctk.StringVar()
        self.class_facility_bool = ctk.BooleanVar()
        self.facilities = ('Football', 'Sixth Form Room', 'Basketball', 'Cricket', 'Multi-Purpose Hall', 'Fitness Suite')
        self.classes = ('9A', '9B', '9C', '9D', '10A', '10B', '10C', '10D', '11A', '11B', '11C', '11D', '12A', '12B', '12C', '12D', '13A', '13B', '13C', '13D')
        #Widgets
        ctk.CTkLabel(self, text = 'Add User', font = ('Impact', 70)).place(anchor = 'center', relx = 0.5, rely = 0.17)
        ctk.CTkLabel(self, text = 'First Name', font = ('Impact', 20)).place(anchor = 'center', relx = 0.2, rely = 0.32)
        ctk.CTkEntry(self, textvariable = self.first_name, width = 215, border_color = 'black', border_width = 2, corner_radius = 0).place(anchor = 'center', relx = 0.3, rely = 0.37)
        ctk.CTkLabel(self, text = 'Last Name', font = ('Impact', 20)).place(anchor = 'center', relx = 0.6, rely = 0.32)
        ctk.CTkEntry(self, textvariable = self.last_name, width = 215, border_color = 'black', border_width = 2, corner_radius = 0).place(anchor = 'center', relx = 0.7, rely = 0.37)
        ctk.CTkLabel(self, text = 'User ID', font = ('Impact', 20)).place(anchor = 'center', relx = 0.18, rely = 0.47)
        ctk.CTkEntry(self, textvariable = self.user_id, width = 215, border_color = 'black', border_width = 2, corner_radius = 0).place(anchor = 'center', relx = 0.3, rely = 0.52)
        ctk.CTkLabel(self, text = 'Occupation', font = ('Impact', 20)).place(anchor = 'center', relx = 0.61, rely = 0.47)
        student_button = ctk.CTkRadioButton(self, text = 'Student', fg_color = 'black', border_color = 'black', hover_color = '#707070', radiobutton_height = 10, radiobutton_width = 10, variable = self.class_facility_bool, value = True, command = self.student_or_teacher)
        student_button.place(anchor = 'center', relx = 0.62, rely = 0.52)
        ctk.CTkLabel(self, text = 'Facility', font = ('Impact', 20))
        teacher_button = ctk.CTkRadioButton(self, text = 'Teacher', fg_color = 'black', border_color = 'black', hover_color = '#707070', radiobutton_height = 10, radiobutton_width = 10, variable = self.class_facility_bool, value = False, command = self.student_or_teacher)
        teacher_button.place(anchor = 'center', relx = 0.8, rely = 0.52)
        self.Label = ctk.CTkLabel(self, text = 'Select Occupation', font = ('Impact', 20))
        self.Label.place(anchor = 'center', relx = 0.5, rely = 0.62)
        self.grade_facility_combobox = ctk.CTkComboBox(self, border_color = 'black', button_color = 'black', state = 'disabled', variable = self.class_facility, values = '', width = 215, dropdown_font = ('Impact', 15))
        self.grade_facility_combobox.place(anchor = 'center', relx = 0.5, rely = 0.67)
        ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text = "Add", text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = self.add_records_func).place(anchor = 'center', relx = 0.5, rely = 0.86)

    #A method to carry out the backend process of error checking the page and inputting the values of the entry boxes into the database through a new record.
    def add_records_func(self):
        #Gets the user id from the database if it exists.
        Id_db = cursor.execute('SELECT user_id FROM User WHERE user_id = ?', (self.user_id.get(),)).fetchall()
        #Checks if all fields are filled out.
        if self.user_id.get() == '' or self.first_name.get() == '' or self.last_name.get() == '' or self.class_facility.get() == '':
            messagebox.showerror("Add Failed", "All fields must be filled out.")
        #Checks if the user exists.
        elif Id_db != []:
            messagebox.showerror("Add Failed", "User already exists")
        #Checks if a wrong occuptation is chosen.
        #Example: S3465 and occupation chosen was a teacher.
        elif (self.user_id.get()[0] == 'S' and not self.class_facility_bool.get()) or (self.user_id.get()[0] == 'T' and self.class_facility_bool.get()):
            messagebox.showerror("Add Failed", "A student or teacher cannot have their code start with a T or S respectively.")
        else:
            #Checks if the admin is adding a student or teacher.
            if self.class_facility_bool.get():
                cursor.execute('INSERT INTO User (user_id, first_name, last_name, class_grade) VALUES (?, ?, ?, ?)', (self.user_id.get(), self.first_name.get(), self.last_name.get(), self.class_facility.get()))
            else:
                cursor.execute('INSERT INTO User (user_id, facility_id, first_name, last_name) VALUES (?, ?, ?, ?)', (self.user_id.get(), self.class_facility.get(), self.first_name.get(), self.last_name.get()))
            conn.commit()
            messagebox.showerror("Add Successful", f'Successfully added {self.first_name.get()} {self.last_name.get()}')

    #A method to display different values in the combo box for a chosen role.
    def student_or_teacher(self):
        if self.class_facility_bool.get():
            self.Label.configure(text = 'Select Class')
            self.grade_facility_combobox.configure(values = self.classes, state = 'readonly')
        else:
            self.Label.configure(text = 'Select Facility')
            self.grade_facility_combobox.configure(values = self.facilities, state = 'readonly')
        
#Facility Support
    def facility_support(self):
        self.clear_frame()
        #Variables
        self.problem = ctk.StringVar()
        self.facility = ctk.StringVar()
        self.other_bool = ctk.BooleanVar()
        self.problems = ['Facility Damage', 'Facility Resources Empty', 'Theft of Facility Equipment', 'Health Hazard']
        self.facilities = ('Football', 'Sixth Form Room', 'Basketball', 'Cricket', 'Multi-Purpose Hall', 'Fitness Suite')

        #Widgets
        ctk.CTkLabel(self, text = 'Facility Support', font = ('Impact', 90)).place(anchor = 'center', relx = 0.5, rely = 0.15)
        ctk.CTkLabel(self, text = 'Choose Facility', font = ('Impact', 40)).place(anchor = 'center', relx = 0.3, rely = 0.35)
        ctk.CTkComboBox(self, state = 'readonly', border_color = 'black', button_color = 'black', variable = self.facility, values = self.facilities, width = 250, dropdown_font = ('Impact', 15)).place(anchor = 'center', relx = 0.7, rely = 0.35)
        ctk.CTkLabel(self, text = 'Choose Problem', font = ('Impact', 37)).place(anchor = 'center', relx = 0.3, rely = 0.5)
        self.problem_combobox = ctk.CTkComboBox(self, state = 'readonly', border_color = 'black', button_color = 'black', width = 250, dropdown_font = ('Impact', 15), variable = self.problem, values = self.problems)
        self.problem_combobox.place(anchor = 'center', relx = 0.7, rely = 0.5)
        self.other_button = ctk.CTkSwitch(self, text = 'Other', command = self.other, variable = self.other_bool, progress_color = theme_color, button_color = 'black')
        self.other_button.place(anchor = 'center', relx = 0.5, rely = 0.6)
        self.other_texbox = ctk.CTkTextbox(self, state = 'disabled', width = 400, height = 100, border_color = 'black', border_width = 2)
        self.other_texbox.place(anchor = 'n', relx = 0.5, rely = 0.65)
        self.submit_button = ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', text = 'Submit', font = ('Impact', 20), command = self.request_problem)
        self.submit_button.place(anchor = 'center', relx = 0.5, rely = 0.9)        

#Reset Content Frame
    def clear_frame(self):
        #This cycles through every widget in the content frame and destroys each widget.
        for widget in self.winfo_children():
            widget.destroy()

class SideBar(ctk.CTkFrame):
    #A constructor method which defines itself, where the frame will be sitting on top off, the details of the user and their card, and the content frame class.
    def __init__(self, parent, login, page):
        #A super constructor method which defines the frame's attributes from which this class inherits from.
        super().__init__(parent, width = 200, height = 600, border_color = "black", border_width = 2, corner_radius = 0, fg_color = '#F0F0F0')
        #Image file load
        profile_icon = ctk.CTkImage(light_image = Image.open("Images/profile.png"), size = (70,70))
        #Widgets
        ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text = '', image = profile_icon, width = 100, height = 100, text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = page.account_edit_page).place(anchor = 'center', relx = 0.5, rely = 0.15)
        ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, width = 180, text = 'Tap In', text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = page.card_tap_in_page).place(anchor = 'center', relx = 0.5, rely = 0.3)
        ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, width = 180, text = 'Analytics', text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = page.analytics_page).place(anchor = 'center', relx = 0.5, rely = 0.6)
        if login.user.user_id[0] == 'A' or login.user.user_id[0] == 'T':
            ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, width = 180, text = 'Schedule Viewer', text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = page.schedule_viewer).place(anchor = 'center', relx = 0.5, rely = 0.4)
            ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, width = 180, text = 'Approvals', text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = page.approval_management).place(anchor = 'center', relx = 0.5, rely = 0.5)
            if login.user.user_id[0] == 'A':
                ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, width = 180, text = 'View Users', text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = page.all_records_page).place(anchor = 'center', relx = 0.5, rely = 0.7)
                ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, width = 180, text = 'Add Users', text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = page.add_records_page).place(anchor = 'center', relx = 0.5, rely = 0.8)
        else:
            ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, width = 180, text = 'Facility Support', text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = page.facility_support).place(anchor = 'center', relx = 0.5, rely = 0.4)
            ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, width = 180, text = 'View Sent Approvals', text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = page.approval_management).place(anchor = 'center', relx = 0.5, rely = 0.5)
            ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, width = 180, text = 'Approval Request', text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = page.approval_request).place(anchor = 'center', relx = 0.5, rely = 0.7)
        ctk.CTkButton(self, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, width = 180, text = 'Logout', text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = login.logout_func).place(anchor = 'center', relx = 0.5, rely = 0.93)

#A class which inherits a frame from the customtkinter module
class LoginPage(ctk.CTkFrame):
    #A constructor method which defines itself, where the frame will be sitting on top off and the details of the user and their card.
    def __init__(self, parent, user = None, card = None):
        #A super constructor method which defines the frame's attributes from which this class inherits from.
        super().__init__(parent, width = 200, height = 600, border_color = "black", border_width = 2, corner_radius = 0, fg_color = '#F0F0F0')
        window.geometry('600x600')
        remove_widgets_login_register()
        
        #Variables
        self.id_entry = ctk.StringVar()
        self.password_entry = ctk.StringVar()
        self.user = user
        self.card = card

        #Image files loaded ready to be used.
        password_icon = ctk.CTkImage(light_image = Image.open("Images/padlock.png"), size = (22,22))
        id_icon = ctk.CTkImage(light_image = Image.open("Images/id.png"), size = (22,22))
        hide_button = ctk.CTkImage(light_image = Image.open("Images/hide.png"), size = (22,22))
        
        #Login frame which sits on top of the window to add a boxy aesthetic look.
        login_frame = ctk.CTkFrame(window_frame, width = 500, height = 500, border_color = 'black', border_width = 2, fg_color = '#F0F0F0', corner_radius = 0)
        login_frame.place(anchor = 'center', relx = 0.5, rely = 0.5)

        #Displayed Widgets
        ctk.CTkLabel(login_frame, text = 'User Login', font = ('Impact', 70)).place(anchor = 'center', relx = 0.5, rely = 0.25)
        ctk.CTkLabel(login_frame, text = '', image = id_icon).place(anchor = 'center', relx = 0.33, rely = 0.4)
        ctk.CTkLabel(login_frame, text = 'User ID', font = ('Impact', 20)).place(anchor = 'center', relx = 0.42, rely = 0.4)
        ctk.CTkEntry(login_frame, textvariable = self.id_entry, width = 200, border_color = 'black', border_width = 2, corner_radius = 0).place(anchor = 'center', relx = 0.5, rely = 0.45)
        ctk.CTkLabel(login_frame, text = '', image = password_icon).place(anchor = 'center', relx = 0.33, rely = 0.525)
        ctk.CTkLabel(login_frame, text = 'Password', font = ('Impact', 20)).place(anchor = 'center', relx = 0.44, rely = 0.53)
        #An object for the password entry field is created as it will be used in another function later.
        self.password = ctk.CTkEntry(login_frame, textvariable = self.password_entry, show = '*', width = 200, border_color = 'black', border_width = 2, corner_radius = 0)
        self.password.place(anchor = 'center', relx = 0.5, rely = 0.58)
        ctk.CTkButton(login_frame, text = '', image = hide_button, hover_color = '#d4d4d4', border_color = 'black', width = 10, border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = self.password_hide).place(anchor = 'center', relx = 0.74, rely = 0.58)
        ctk.CTkButton(login_frame, text = 'Login', hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 25), command = self.login_func).place(anchor = 'center', relx = 0.5, rely = 0.7)
        ctk.CTkLabel(login_frame, text = 'or').place(anchor = 'center', relx = 0.5, rely = 0.77)
        ctk.CTkButton(login_frame, text = "Don't have an account? Register Here", hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = lambda: RegisterPage(window_frame)).place(anchor = 'center', relx = 0.5, rely = 0.84)

    #A method which creates a student and card object to login the user into the system.
    def login_func(self):
        #Gets all the user's data from the database.
        self.user_db = cursor.execute('''SELECT * 
                                      FROM User 
                                      WHERE user_id = ?;''', 
                                      (self.id_entry.get(),)).fetchall()
        #Checks if the user has an existing password or not and shows an appropriate message.
        if self.user_db[0][4] == None:
            messagebox.showerror('Login Failed', 'Please set a new password.')
        #Checks if the password is correct.
        elif self.password_check():
            #Gets the card assigned to the user from the database.
            self.card_db = cursor.execute('''SELECT card_id, tag_id 
                                       FROM Card 
                                       WHERE user_id = ?;''', 
                                       (self.user_db[0][0],)).fetchall()
            #Creates two objects to store the values of the user and their card and shows an appropriate message welcoming the user.
            self.card, self.user = Card(self.card_db[0][0], self.card_db[0][1]), User(self.user_db[0][0], self.user_db[0][2], self.user_db[0][3], self.user_db[0][4], self.user_db[0][5], self.user_db[0][6], self.user_db[0][1])
            messagebox.showinfo('Login Successful', f'Welcome, {self.user_db[0][2]} {self.user_db[0][3]}')
            #Goes back to the main function with login having a value rather than none.
            main(self)
        else:
            messagebox.showerror("Login Failed", "Incorrect username or password")

    #A method to check if the password the user enter matches the constructed one from the database.
    def password_check(self):
        #This combines the user's entry with the salt on the database.
        salted_password = self.password_entry.get().encode('utf-8') + self.user_db[0][5]
        #This hashes the salted_password.
        hashed_password = hashlib.sha256(salted_password).hexdigest()
        #This compares the password with the one on the database and returns True if it is.
        if hashed_password == self.user_db[0][4]: return True
        else: return False

    #A method which hides and unhides the password depending if the user clicks a button.
    def password_hide(self):
        if self.password.cget('show') == '*':
            self.password.configure(show = '')
        else:
            self.password.configure(show = '*')

    #This method deletes itself and takes the user back to the login screen.
    def logout_func(self):
        messagebox.showinfo('Logout Successful', f'Goodbye, {self.user_db[0][2]} {self.user_db[0][3]}')
        remove_widgets_login_register()
        #Deletes itself
        del self
        main(login = None)

#A class which inherits a frame from the customtkinter module
class RegisterPage(ctk.CTkFrame):
    #A constructor method which defines itself, where the frame will be sitting on top off.
    def __init__(self, parent):
        #A super constructor method which defines the frame's attributes from which this class inherits from.
        super().__init__(parent, width = 200, height = 600, border_color = "black", border_width = 2, corner_radius = 0, fg_color = '#F0F0F0')    
        remove_widgets_login_register()

        #Variables
        self.id_entry = ctk.StringVar()
        self.password_entry = ctk.StringVar()
        self.confirm_password_entry = ctk.StringVar()
        
        #Image files loaded ready to be used.
        hide_button = ctk.CTkImage(light_image = Image.open("Images/hide.png"), size = (22,22))

        #Login frame which sits on top of the window to add a boxy aesthetic look.
        login_frame = ctk.CTkFrame(window_frame, width = 500, height = 500, border_color = "black", fg_color = '#F0F0F0', border_width = 2, corner_radius = 0)
        login_frame.place(anchor = 'center', relx = 0.5, rely = 0.5)

        #Widgets
        ctk.CTkLabel(login_frame, text = 'Set New Password', font = ('Impact', 60)).place(anchor = 'center', relx = 0.5, rely = 0.17)
        ctk.CTkLabel(login_frame, text = 'User ID', font = ('Impact', 20)).place(anchor = 'center', relx = 0.5, rely = 0.3)
        ctk.CTkEntry(login_frame, textvariable = self.id_entry, width = 190, border_color = 'black', border_width = 2, corner_radius = 0).place(anchor = 'center', relx = 0.5, rely = 0.35)
        ctk.CTkLabel(login_frame, text = 'Password', font = ('Impact', 20)).place(anchor = 'center', relx = 0.5, rely = 0.45)
        #An object for the password and confirm password entry field is created as it will be used in another function later.
        self.password = ctk.CTkEntry(login_frame, textvariable = self.password_entry, width = 190, border_color = 'black', border_width = 2, corner_radius = 0)
        self.password.place(anchor = 'center', relx = 0.5, rely = 0.5)
        ctk.CTkLabel(login_frame, text = 'Confirm Password', font = ('Impact', 20)).place(anchor = 'center', relx = 0.5, rely = 0.6)
        self.confirm_password = ctk.CTkEntry(login_frame, textvariable = self.confirm_password_entry, width = 190, border_color = 'black', border_width = 2, corner_radius = 0)
        self.confirm_password.place(anchor = 'center', relx = 0.5, rely = 0.65)

        ctk.CTkButton(login_frame, hover_color = '#d4d4d4', border_color = 'black', width = 10, border_width = 2, text = '', image = hide_button, text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = self.password_hide).place(anchor = 'center', relx = 0.73, rely = 0.5)
        ctk.CTkButton(login_frame, hover_color = '#d4d4d4', border_color = 'black', width = 10, border_width = 2, text = '', image = hide_button, text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = self.confirm_password_hide).place(anchor = 'center', relx = 0.73, rely = 0.65)
        ctk.CTkButton(login_frame, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text = 'Set New Password', text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = self.register_new_password_func).place(anchor = 'center', relx = 0.5, rely = 0.79)
        ctk.CTkLabel(login_frame, text = 'or').place(anchor = 'center', relx = 0.5, rely = 0.86)
        ctk.CTkButton(login_frame, hover_color = '#d4d4d4', border_color = 'black', border_width = 2, text = "Go to Login", text_color = 'black', fg_color = 'white', font = ('Impact', 20), command = lambda: LoginPage(window_frame)).place(anchor = 'center', relx = 0.5, rely = 0.93)

    #Two methods which hides and unhides the password depending if the user clicks a button.
    def password_hide(self):
        #If user presses on the button and it shows the password then it shows the password letters as '*' and vice versa
        if self.password.cget('show') == '*':
            self.password.configure(show = '')
        else:
            self.password.configure(show = '*')

    def confirm_password_hide(self):
        if self.confirm_password.cget('show') == '*':
            self.confirm_password.configure(show = '')
        else:
            self.confirm_password.configure(show = '*')

    #A method for the backend function of the register page.
    def register_new_password_func(self):
        #This uses the 're' module to create a regular expression for the password checks.
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        user_db = cursor.execute('SELECT user_id, hashed_password FROM user WHERE user_id = ?', (self.id_entry.get(),)).fetchall()
        if user_db != []:
            #This checks if the user has logged in before or not by checking if they have a password.
            if user_db[0][1] == None:
                #This checks if all fields are not empty and shows an appropriate error message.
                if self.id_entry.get() == '' or self.password_entry.get() == '' or self.confirm_password_entry.get() == '':
                    messagebox.showerror("Register Failed", "All fields must be filled out.")
                #This checks if both the password and confirm password values the user inputed are the same and shows an appropriate error message.
                elif self.password_entry.get() != self.confirm_password_entry.get():
                    messagebox.showerror("Register Failed", "Please make sure the passwords are the same.")
                #This checks the password inputed against the password checks and shows an appropriate error message.
                elif not re.match(pattern, self.password_entry.get()):
                    messagebox.showerror("Register Failed", "Password is not strong enough. Please include: 8 Characters minimum, A capital letter, A small letter, A number, A symbol.")
                elif re.match(pattern, self.password_entry.get()):
                    #This retrieves a hashed password from the user's input and a random salt from a function.
                    hashed_password, salt = self.password_hash()
                    #This retrieves the next available card which is not taken by a user.
                    card = cursor.execute('SELECT card_id FROM Card WHERE user_id IS NULL LIMIT 1;').fetchall()
                    #This updates the card record that was retrieved with the new user who owns it.
                    if card != []:
                        cursor.execute('''UPDATE Card 
                                    SET user_id = ? 
                                    WHERE card_id = ?;''', 
                                    (self.id_entry.get(), card[0][0]))
                        #This stores the hashed password and salt that were created.
                        cursor.execute('''UPDATE User 
                                    SET hashed_password = ?, salt = ?
                                    WHERE user_id = ?;''', 
                                    (hashed_password, salt, self.id_entry.get()))
                        #This shows an appropriate message to let the user know the password has been set successfully.
                        messagebox.showinfo('Password Successfully Set', 'Please login with the new password.')
                        conn.commit()
                        #Takes you back to the login page.
                        LoginPage(window_frame)
                    else:
                        messagebox.showerror("Password Set Failed", "There are no available cards at this time, please check back again in some time.")
            else:
                messagebox.showerror("Password Set Failed", "Accounts password has already been changed please change from user settings.")
        else:
            messagebox.showerror("Password Set Failed", "User doesn't exist.")
    
    #A function to hash passwords
    def password_hash(self):
        #A random salt of 16 bytes is generated
        salt = secrets.token_bytes(16)
        #The salted password is the user's password with the salt that was previously generated appended to the end.
        salted_password = self.password_entry.get().encode('utf-8') + salt
        #The hashed password is the salted password put through a hashing algorithm and represented as a hexadecimal.
        hashed_password = hashlib.sha256(salted_password).hexdigest()
        return hashed_password, salt

def remove_widgets_login_register():
    #Removes every widget on the page by cyclying through them and destroying them.
    for widget in window_frame.winfo_children():
        widget.destroy()

def get_theme_color():
    color_picker = ColorChooserDialog()
    color_picker.show()
    color = color_picker.result
    theme_color = color.hex
    window.mainloop()

def email(subject, body):
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login('3465@ascsdubai.ae', 'Mario@School24')
        smtp.sendmail('3465@ascsdubai.ae', 'skatedany26@gmail.com', f'Subject: {subject}\n\n{body}')

#This is a standard function to check whether a login object was created or not and shows the main menu screen or the login screen respectively. 
def main(login = None):
    if login != None:
        #Calls the remove_widgets_login_register() function.
        remove_widgets_login_register()
        #Sets the geometry of the screen to a larger size.
        window.geometry('900x600')
        #Creates an object through the ContentFrame class called page.
        page = ContentFrame(window_frame, login.user, login.card)
        #Creates an object through the SideBar class called sidebar.
        sidebar = SideBar(window_frame, login, page)
        #Places the top left of the sidebar object at top left of the screen.
        sidebar.place(anchor = 'nw', relx = 0, rely = 0)
        #Places the center of the page object slightly off centered to the right.
        page.place(anchor = 'center', relx = 0.61, rely = 0.5)
    else:
        #Creates an object through the LoginPage class.
        login = LoginPage(window_frame)

#This is a constructor which checks if this program is being run as the main file.
if __name__ == '__main__':
    #Calls the main() function
    main(login = None)
    #Calls the windows mainloop method to prevent the window from closing
    window.mainloop()
