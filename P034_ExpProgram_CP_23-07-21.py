#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 9 2023
@author: cyruskirkman

This is the main code for Dr. Fang's P034b project studying the role of feedback
upon response accuracy (and maybe learning acquisition) in a delayed match-to-
sample task (DMTS). It is an alternative approach to the previous three-button
layout approoach, in the hopes of both improving baseline accuracy but also 
better observing a learning curve from 50% (chance) accuracy over time,
dependent upon feedback. Instead, the layout included two statically colored 
and placed buttons on L/R sides of the screen with a dynamically changing
center stimulus. L/R key accuracy was dependent upon the image type and was
fixed accross sessions. Trainings are as follows
    
    1) Mixed instrumental/autoshaping: one of the three stimuli were filled in
        at the beginning of each trial. After a peck on the filled stimulus (FR1),
        a reinforcer was immediately provided. If no response was made within 
        10 s, a reinforcer was immediately provided. Fill colors were either blue
        or yellow, save for six trials for the first two sessions that were grey.
        
    2) Match to sample: The next phase was a simple MTS task in which a color
        was presented in the sample slot. After several pecks (FR3 to start,
        then inreased to FR10), a blue and yellow option were presented in 
        each of the comparison locations below (randomly assigned per trial) 
        while the sample remained filled in. A peck on the correct comparison
        key (e.g., blue comparison in the context of a blue sample) was
        immediately reinforced, while an incorrect choice (e.g., yellow
        comparison in the context of the blue sample) was punished with a 10s
        timeout before the ITI and next trial. Subjects proceeded to the next
        phase after they demonstrated at least 85% accuracy on a completed 
        session
    
    3) Delayed match to sample: Similar to the prior MTS phase, the DMTS started
        with presentation of the sample and completion of a FR10 schedule to 
        proceed. Next, the sample dissapeared and birds faced a delay period 
        of variable length: either 2, 4, 8, or 16 s. After the delay concluded,
        the two differently filled comparison choice options appeared. When a
        choice was made, subjects were presented with a post-choice interval
        in which the sample key (which had been empty) was manipulated in a 
        manner dependent upon the group subjects were assigned: birds in the
        control group faced a filled grey key for every post-choice interval. 
        Birds in the experimental group faced a re-presentation of the sample
        color from the start of the trial. After the 3s post-choice interval,
        a correct choice was reinforced with food while and incorrect choice 
        was punished with a 10s TO.
"""
# The first variable declared is whether the program is the operant box version
# for pigeons, or the test version for humans to view. The variable below is 
# a T/F boolean that will be referenced many times throughout the program 
# when the two options differ (for example, when the Hopper is accessed or
# for onscreen text, etc.). It needs to be changed manually based on whether
# the program is running in operant boxes (True) or not (False).
operant_box_version = False

# Prior to running any code, its conventional to first import relevant 
# libraries for the entire script. These can range from python libraries (sys)
# or sublibraries (setrecursionlimit) that are downloaded to every computer
# along with python, or other files within this folder (like control_panel or 
# maestro).
# =============================================================================
from csv import writer, QUOTE_MINIMAL, DictReader
from datetime import datetime, timedelta, date
from sys import setrecursionlimit, path as sys_path
from tkinter import Toplevel, Canvas, BOTH, TclError, Tk, Label, Button, \
     StringVar, OptionMenu, IntVar, Radiobutton
from time import time
from os import getcwd, mkdir, path as os_path
from random import choice, shuffle
from PIL import ImageTk, Image  


# Import hopper/other specific libraries from files on operant box computers
try:
    if operant_box_version:
        sys_path.insert(0, str(os_path.expanduser('~')+"/OneDrive/Desktop/Hopper_Software"))
        import graph
        import polygon_fill
        from hopper import HopperObject
except ModuleNotFoundError:
    input("ERROR: Cannot find hopper hardware. Should you change operant box version to 'FALSE'?")

# Below  is just a safety measure to prevent too many recursive loops). It
# doesn't need to be changed.
setrecursionlimit(5000)

"""
The code below jumpstarts the loop by first building the hopper object and 
making sure everything is turned off, then passes that object to the
control_panel. The program is largely recursive and self-contained within each
object, and a macro-level overview is:
    
    ControlPanel -----------> MainScreen ------------> PaintProgram
         |                        |                         |
    Collects main           Runs the actual         Gets passed subject
    variables, passes      experiment, saves        name, but operates
    to Mainscreen          data when exited          independently
    

"""

# The first of two objects we declare is the ExperimentalControlPanel (CP). It
# exists "behind the scenes" throughout the entire session, and if it is exited,
# the session will terminate.
class ExperimenterControlPanel(object):
    # The init function declares the inherent variables within that object
    # (meaning that they don't require any input).
    def __init__(self):
        # First, setup the data directory in "Documents"
        self.doc_directory = str(os_path.expanduser('~'))+"/Documents/"
        # Next up, we need to do a couple things that will be different based
        # on whether the program is being run in the operant boxes or on a 
        # personal computer. These include setting up the hopper object so it 
        # can be referenced in the future, or the location where data files
        # should be stored.
        if operant_box_version:
            # Setup the data directory in "Documents"
            self.doc_directory = str(os_path.expanduser('~'))+"/Documents/"
            self.data_folder = "P034b_data" # The folder within Documents where subject data is kept
            self.data_folder_directory = str(os_path.expanduser('~'))+"/OneDrive/Desktop/Data/" + self.data_folder
        # Set hopper object to be a variable of self, so it can be referenced...
            self.Hopper = HopperObject()
        else: # If not, just save in the current directory the program us being run in 
            self.data_folder_directory = getcwd() + "/Data/"
            self.Hopper = None
        
        # setup the root Tkinter window
        self.control_window = Tk()
        self.control_window.title("P034b Control Panel")
        ##  Next, setup variables within the control panel
        # Subject ID
        self.pigeon_name_list = ["Luigi", "Waluigi","Wario","Peach", "Wenchang"]
        self.pigeon_name_list.sort() # This alphabetizes the list
        self.pigeon_name_list.insert(0, "TEST")
        
        Label(self.control_window, text="Pigeon Name:").pack()
        self.subject_ID_variable = StringVar(self.control_window)
        self.subject_ID_variable.set("Select")
        self.subject_ID_menu = OptionMenu(self.control_window,
                                          self.subject_ID_variable,
                                          *self.pigeon_name_list,
                                          command=self.set_pigeon_ID).pack()
        
        # Training phases
        Label(self.control_window, text = "Select phase:").pack()
        self.training_phase_variable = IntVar()
        self.training_phase_name_list = ["1: Many-to-One",
                                    "2: Delayed Many-to-One",
                                    "3: Auto-shaping"]
        for t_name in self.training_phase_name_list:
            Radiobutton(self.control_window,
                        variable = self.training_phase_variable,
                        text = t_name,
                        value = self.training_phase_name_list.index(t_name)).pack()
        self.training_phase_variable.set(1) # Default set to first training phase
        
        # Stimulus set
        self.stimuli_titles = ["1: Stimulus set 1 (Anchor...)",
                               "2: Stimulus set 2 (Asparagus...)",
                               "3: Stimulus set 3 (BlueTable...)",
                               "4: Stimulus set 4 (Apple...)",
                               "5: Stimulus set 5 (Bell...)",
                               "6: Stimulus set 6 (Barn...)",
                               "7: Stimulus set 7 (Box...)"]
        
        Label(self.control_window, text="Stimulus Set:").pack()
        self.stimulus_set_variable = StringVar(self.control_window)
        self.stimulus_set_variable.set("Select")
        self.stimulus_set_menu = OptionMenu(self.control_window,
                                          self.stimulus_set_variable,
                                          *self.stimuli_titles
                                          ).pack()
        
        # Correction procedure 
# =============================================================================
#         Label(self.control_window,
#               text = "Correction procedure?").pack()
#         self.correction_procedure_var = IntVar()
#         self.correction_procedure_var1 =  Radiobutton(self.control_window,
#                                    variable = self.correction_procedure_var,
#                                    text = "Yes",
#                                    value = True).pack()
#         self.correction_procedure_var2 = Radiobutton(self.control_window,
#                                   variable = self.correction_procedure_var,
#                                   text = "No",
#                                   value = False).pack()
#         self.correction_procedure_var.set(False) # Default set to False
# =============================================================================
        
# =============================================================================
#         # MTO FR selection
#         Label(self.control_window,
#               text = "MTO FR:").pack()
#         self.MTO_FR_stringvar = StringVar()
#         self.MTO_FR_variable = Entry(self.control_window, 
#                                      textvariable = self.MTO_FR_stringvar).pack()
#         self.MTO_FR_stringvar.set("3")
# =============================================================================
        
        # Record data variable?
        Label(self.control_window,
              text = "Record data in seperate data sheet?").pack()
        self.record_data_variable = IntVar()
        self.record_data_rad_button1 =  Radiobutton(self.control_window,
                                   variable = self.record_data_variable, text = "Yes",
                                   value = True).pack()
        self.record_data_rad_button2 = Radiobutton(self.control_window,
                                  variable = self.record_data_variable, text = "No",
                                  value = False).pack()
        self.record_data_variable.set(True) # Default set to True
        
        
        # Start button
        self.start_button = Button(self.control_window,
                                   text = 'Start program',
                                   bg = "green2",
                                   command = self.build_chamber_screen).pack()
        
        # This makes sure that the control panel remains onscreen until exited
        self.control_window.mainloop() # This loops around the CP object
        
        
    def set_pigeon_ID(self, pigeon_name):
        # This function checks to see if a pigeon's data folder currently 
        # exists in the respective "data" folder within the Documents
        # folder and, if not, creates one.
        if operant_box_version:
            try:
                if not os_path.isdir(self.data_folder_directory + pigeon_name):
                    mkdir(os_path.join(self.data_folder_directory, pigeon_name))
                    print("\n ** NEW DATA FOLDER FOR %s CREATED **" % pigeon_name.upper())
            except FileExistsError:
                print("Data folder for %s exists." % pigeon_name)       
        else:
            parent_directory = getcwd() + "/data/"
            if not os_path.isdir(parent_directory + pigeon_name):
                mkdir(os_path.join(parent_directory, pigeon_name))
                print("\n ** NEW DATA FOLDER FOR %s CREATED **" % pigeon_name.upper())
                
                
    def build_chamber_screen(self):
        # Once the green "start program" button is pressed, then the mainscreen
        # object is created and pops up in a new window. It gets passed the
        # important inputs from the control panel.
        print(str(self.stimulus_set_variable.get())[0])
        if self.subject_ID_variable.get() in self.pigeon_name_list:
            if self.stimulus_set_variable.get() in self.stimuli_titles:
                print(f"{'SESSION STARTED': ^15}")
                self.MS = MainScreen(
                    self.Hopper,
                    str(self.subject_ID_variable.get()), # subject_ID
                    self.record_data_variable.get(), # Boolean for recording data (or not)
                    self.data_folder_directory, # directory for data folder
                    self.training_phase_variable.get(), # Which training phase
                    self.training_phase_name_list, # list of training phases
                    int(str(self.stimulus_set_variable.get())[0])
                    #self.MTO_FR_stringvar.get(), # MTO FR
                    #self.correction_procedure_var.get() # Correction procedure auto-shaping boolean
                    )
            else:
                print("\n ERROR: Input Stimulus Set Before Starting Session")
        else:
            print("\n ERROR: Input Correct Pigeon ID Before Starting Session")
            

# Then, setup the MainScreen object
class MainScreen(object):
    # First, we need to declare several functions that are 
    # called within the initial __init__() function that is 
    # run when the object is first built:
    
    def __init__(self, Hopper, subject_ID, record_data, data_folder_directory,
                 training_phase, training_phase_name_list, #MTO_FR, correction_procedure
                 stimulus_set_num):
        ## Firstly, we need to set up all the variables passed from within
        # the control panel object to this MainScreen object. We do this 
        # by setting each argument as "self." objects to make them global
        # within this object.
        
        # Setup training phase
        self.training_phase = training_phase # the phase of training as a number (0-2)
        if self.training_phase == 2: # if autoshaping
            self.illuminated_key = "NA" # set up key variable
        self.training_phase_name_list = training_phase_name_list
        self.stimulus_set_num = stimulus_set_num
        # Setup data directory
        self.data_folder_directory = data_folder_directory
        
        ## Set the other pertanent variables given in the command window
        self.subject_ID = subject_ID
        self.record_data = record_data
        #self.MTO_FR = int(MTO_FR) # Number of times the oberving key should be pressed for the target to appear 
        #self.correction_procedure = correction_procedure # Boolean
        self.previous_trial_correct = True # Default true
        self.feedback_duration = "NA" # This is set in the feedback stage of DMTO trials
        
        # In order to properly counter-balance both the correct key assignment
        # (either left or right) and the sample feedback type (informative vs.
        # non-informative) for each stimulus, subjects were assigned to one of
        # four groups, which were organized as follows. Note that all subjects
        # recieved all COMBINATIONS of stimuli (e.g., all within-subjects),
        # and this table only represents the first 1/4 of stimul (i.e., 2).
        #
        #      Informative   Non-Informative
        #         ____________________
        #        |         |          |
        #   Left |    1    |     2    |
        #        |_________|__________|
        #        |         |          |
        #  Right |    3    |     4    |
        #        |_________|__________|
        #
        
        dict_of_subject_assignments = {
            "TEST": 1,
            "Wario": 1,
            "Durrell": 1,
            "Peach": 2,
            "Jubilee": 2,
            "Luigi": 3,
            "Wenchang": 3,
            "Waluigi": 4,
            "Hawthorne": 4
            }
        
        self.exp_condition = dict_of_subject_assignments[self.subject_ID]

        # Set up sample key FR
        if (self.training_phase == 0): # If MTO (no delay)
            self.sample_key_FR = 5 # int(MTO_FR)
        elif self.training_phase == 2: # If auto-shaping
            self.sample_key_FR = 1
        else:
            self.sample_key_FR = 8 # Default is 8, TBD each ITI
            
        self.trial_FR = "NA"
        
        ## Set up the visual Canvas
        self.root = Toplevel()
        self.root.title(f"P034b{self.stimulus_set_num}: Feedback in DMTO: " + 
                        self.training_phase_name_list[self.training_phase][3:]) # this is the title of the windows
        self.mainscreen_height = 600 # height of the experimental canvas screen
        self.mainscreen_width = 800 # width of the experimental canvas screen
        self.root.bind("<Escape>", self.exit_program) # bind exit program to the "esc" key
        
        # If the version is the one running in the boxes...
        if operant_box_version: 
            # Keybind relevant keys
            self.cursor_visible = True # Cursor starts on...
            self.change_cursor_state() # turn off cursor UNCOMMENT
            self.root.bind("<c>", lambda event: self.change_cursor_state()) # bind cursor on/off state to "c" key
            
            # Then fullscreen (on a 800x600p screen)
            self.root.attributes('-fullscreen', True)
            self.mastercanvas = Canvas(self.root,
                                   bg="black")
            self.mastercanvas.pack(fill = BOTH,
                                   expand = True)
        # If we want to run a "human-friendly" version
        else: 
            # No keybinds and  800x600p fixed window
            self.mastercanvas = Canvas(self.root,
                                   bg="black",
                                   height=self.mainscreen_height,
                                   width = self.mainscreen_width)
            self.mastercanvas.pack()
            
        # Setup hopper (passed from the control panel)
        self.Hopper = Hopper
        
        # Timing variables
        self.auto_reinforcer_timer = 10 * 1000 # Time (ms) before reinforcement for AS
        self.start_time = None # This will be reset once the session actually starts
        self.trial_start = None # Duration into each trial as a second count, resets each trial
        self.session_duration = datetime.now() + timedelta(minutes = 90) # Max session time is 90 min
        self.TO_duration = 10 * 1000 # duration of timeout (ms)
        self.ITI_duration = 15 * 1000 # duration of inter-trial interval (ms)
        if self.subject_ID in ["Hawthorne", "Waluigi"]:
            self.hopper_duration = 10000 # duration of accessible hopper(ms)
        else:
            self.hopper_duration = 5000 # duration of accessible hopper(ms)
        self.current_trial_counter = 0 # counter for current trial in session
        self.non_CP_trials = 1 # number of non-correction procedure trials
        self.trial_stage = 0 # Trial substage (4 within DMTO)
        self.trial_delay_duration = 2 * 1000 # 2s; this may is variable
        

        # These are additional "under the hood" variables that need to be declared
        self.max_number_of_reinforced_trials = 96 # Max number of trials within a session
        self.session_data_frame = [] #This where trial-by-trial data is stored
        header_list = ["SessionTime", "Xcord","Ycord", "Event",
                       "CorrectionTrial", "SampleStimulus", "CorrectKey",
                       "StimulusCondition", "TrialSubStage", "TrialTime", 
                       "TrialSubStageTimer","TrialNum", "NonCPTrialNum",
                       "DelayDuration", "FeedbackDuration", "SampleFR",
                       "Subject", "ExpCondition", "TrainingPhase",
                       "StimulusSetNum", "Date"] # Column headers
        self.session_data_frame.append(header_list) # First row of matrix is the column headers
        self.date = date.today().strftime("%y-%m-%d")
        self.myFile_loc = 'FILL' # To be filled later on after Pig. ID is provided (in set vars func below)

        self.control_feedback_color = "dark slate gray"
        self.left_comp_color = "green"
        self.right_comp_color = "red"

        ## Finally, start the recursive loop that runs the program:
        self.place_birds_in_box()

    def place_birds_in_box(self):
        # This is the default screen run until the birds are placed into the
        # box and the space bar is pressed. It then proceedes to the ITI. It only
        # runs in the operant box version. After the space bar is pressed, the
        # "first_ITI" function is called for the only time prior to the first trial
        
        def first_ITI(event):
            # Is initial delay before first trial starts. It first deletes all the
            # objects off the mnainscreen (making it blank), unbinds the spacebar to 
            # the first_ITI link, followed by a 30s pause before the first trial to 
            # let birds settle in and acclimate.
            self.mastercanvas.delete("all")
            self.root.unbind("<space>")
            self.start_time = datetime.now() # Set start time
            self.current_key_stimulus_dict = {
                "left_comparison_key": "black",
                "right_comparison_key": "black",
                "sample_key": "black"
                }
            
            # First set up the path to the stimulus identity .csv document, 
            # which will differ based upon whether you're running this on 
            # a lab computer or PC
            if operant_box_version:
                stimuli_csv_path = f"{str(os_path.expanduser('~'))}/OneDrive/Desktop/P034b/stimuli{self.stimulus_set_num}/P034b_stimuli_assignments{self.stimulus_set_num}.csv"
            else:
               
                stimuli_csv_path = f"stimuli{self.stimulus_set_num}/P034b_stimuli_assignments{self.stimulus_set_num}.csv"
                
            # Import the used sample stimuli, their respective key assignments,
            # and conditional assignments as a lists of dictionaries that are 
            # structured as {'Name': 'C2_Phase1.bmp', 'Key': 'L', 'Group': 'E'}. 
            # The list will be equal to the number of elements in the .csv file
            # and doesn't actually take into account any of the literal files.
            with open(stimuli_csv_path, 'r', encoding='utf-8-sig') as f:
                dict_reader = DictReader(f) 
                self.tenative_stimuli_identity_d_list = list(dict_reader)
        
            
            # After that, let's condense the stimulus dictionary list down for 
            # each of the experimental conditions:
            if self.stimulus_set_num == 1:
               self.stimuli_identity_d_list = self.tenative_stimuli_identity_d_list
            else:
                self.stimuli_identity_d_list = []
                for d in self.tenative_stimuli_identity_d_list:
                    new_dict = {}
                    for k in list(d.keys()):
                        # print(k)
                        if k == "Name":
                            new_dict[k] = d[k]
                        elif str(self.exp_condition) in k:
                            new_dict[k[:-1]] = d[k]
                    self.stimuli_identity_d_list.append(new_dict)
            # print(self.stimuli_identity_d_list)
            
            # Next, pick out the control feedback stimulus (if it exists in 
            # the .csv doc). Note that this shouldn't exist for the first
            # stimulus set, given that the control feedback was created in
            # this program given coordinates/shapes. If stimulus set 5,
            # we creat a dictionary for feedback stimuli
            if self.stimulus_set_num not in [5, 6, 7]:
                for i in self.stimuli_identity_d_list:
                    if i['Key'] == 'S':
                        self.feedback_stimulus = i['Name']
                        self.stimuli_identity_d_list.remove(i)
            else:
                for i in list(range(0,len(self.stimuli_identity_d_list))):
                    # If a control stimulus
                    if "C" in self.stimuli_identity_d_list[i]["Group"]:
                        control_num = self.stimuli_identity_d_list[i]["Group"][1]
                        for stim in self.stimuli_identity_d_list:
                            if stim["Key"] == f"S{control_num}":
                                self.stimuli_identity_d_list[i]["Feedback"] = stim["Name"]
                    # If experimental, feedback is same as sample
                    elif "E" in self.stimuli_identity_d_list[i]["Group"]:
                        self.stimuli_identity_d_list[i]["Feedback"] = self.stimuli_identity_d_list[i]["Name"]
                        
                #print(self.stimuli_identity_d_list)
                                                                
            
            # Once the list of dictionaries is written, we can use it to assign
            # the stimuli to each trial of the session. We do this by writing
            # each of the stimuli to a list (e.g., 1...8), shuffling the order
            # of the list, then apending the elements to the session-wide list
            # until it reaches a number of elements equal to the maximum trials
            # per session.
            self.trial_stimulus_order = []
            while len(self.trial_stimulus_order) < self.max_number_of_reinforced_trials:
                set_of_trials = []
                while len(set_of_trials) < len(self.stimuli_identity_d_list):
                    for i in self.stimuli_identity_d_list:
                        if "S" not in i["Key"]:
                            set_of_trials.append(i["Name"])
                shuffle(set_of_trials)
                for x in set_of_trials:
                    self.trial_stimulus_order.append(x)
                    
            # After the order of stimuli per trial is determined, there are a 
            # couple other things that neeed to occur during the first ITI:
            if self.subject_ID == "TEST": # If test, don't worry about ITI delays
                self.ITI_duration = 1 * 1000
                self.root.after(1, lambda: self.ITI())
            else:
                self.root.after(30000, lambda: self.ITI())

        self.root.bind("<space>", first_ITI) # bind cursor state to "space" key
        self.mastercanvas.create_text(350,300,
                                      fill="white",
                                      font="Times 20 italic bold",
                                      text=f"P034b \n Place bird in box, then press space \n Subject: {self.subject_ID} \n Training Phase {self.training_phase_name_list[self.training_phase]}\n Stimulus set: {self.stimulus_set_num}")
                
    ## %% ITI
    # Every trial (including the first) "starts" with an ITI. The ITI function
    # does several different things:
    #   1) Checks to see if any session constraints have been reached
    #   2) Resets the hopper and any trial-by-trial variables
    #   3) Increases the trial counter by one
    #   4) Moves on to the next trial after a delay
    # 
    def ITI (self):
        # This function just clear the screen. It will be used a lot in the future, too.
        self.clear_canvas()
        
        # Make sure pecks during ITI are saved
        self.mastercanvas.create_rectangle(0,0,
                                           self.mainscreen_width,
                                           self.mainscreen_height,
                                           fill = "black",
                                           outline = "black",
                                           tag = "bkgrd")
        self.mastercanvas.tag_bind("bkgrd",
                                   "<Button-1>",
                                   lambda event, 
                                   event_type = "ITI_peck": 
                                       self.write_data(event, event_type))
        

        # First, check to see if any session limits have been reached (e.g.,
        # if the max time or reinforcers earned limits are reached).
        if  self.non_CP_trials > self.max_number_of_reinforced_trials:
            print("Trial max reached")
            self.exit_program("event")
        # elif datetime.now() >= (self.session_duration):
        #    print("Time max reached")
        #    self.exit_program("event")
        
        # Else, after a timer move on to the next trial. Note that,
        # although the after() function is given here, the rest of the code 
        # within this function is still executed before moving on.
        else: 
            # Print text on screen if a test (should be black if an experimental trial)
            if not operant_box_version or self.subject_ID == "TEST":
                self.mastercanvas.create_text(400,300,
                                              fill="white",
                                              font="Times 20 italic bold",
                                              text=f"ITI ({int(self.ITI_duration/1000)} sec.)")
                
            # This calls the Hopper function to turn it off, and resets other
            # variables. The hopper should be turned off in the previous function,
            # but this is an additional safeguard just to be safe.
            if operant_box_version:
                self.Hopper.change_hopper_state("Off")
                
            # Reset other variables for the following trial.
            self.trial_start = time() # Set trial start time (note that it includes the ITI, which is subtracted later)
            self.trial_substage_start_time = time() # Reset substage timer
            self.write_comp_data(False) # update data .csv with trial data from the previous trial
            self.trial_stage = 0 # Reset trial substage
            self.feedback_duration = "NA" # This is set in the feedback stage of DMTO trials
            self.trial_delay_duration = choice(list(range(2,5))) * 1000
            
            # If an experimental trial is up next (not repeated CP)...
            # if self.current_trial_counter == 0 or not self.correction_procedure or (self.correction_procedure and self.previous_trial_correct): 
            # First pick the sample from the prexisting list....
            self.sample_stimulus = self.trial_stimulus_order[0]
            self.trial_stimulus_order.remove(self.sample_stimulus)
            for i_dict in self.stimuli_identity_d_list:
                if i_dict["Name"] == self.sample_stimulus:
                    self.exp_condition = i_dict["Group"][0] # Either "C" or "E"
                    self.correct_key = i_dict["Key"]
                    if self.stimulus_set_num in [5, 6, 7]:
                        self.feedback_stimulus = i_dict["Feedback"]
            # Next reset the FR if DMTO
            if self.training_phase == 1:
                self.sample_key_FR = choice(list(range(3,9)))
                
            elif self.training_phase == 2:
                as_options = ["left_comparison_key",
                              "right_comparison_key",
                              "sample_key"]
                if self.current_trial_counter > 15: # If white ready signal
                    as_options.append("sample_key")
                # Pick the illuminated key
                self.illuminated_key = choice(as_options)
                    
                print(f"Stimulus Name: {self.sample_stimulus} \nGroup: {self.exp_condition} \nKey: {self.correct_key}\nFR: {self.sample_key_FR}")
   
            # Increase trial counter by one
            self.current_trial_counter += 1
            
            # Next, set a delay timer to proceed to the next trial
            self.root.after(self.ITI_duration, self.ready_signal_phase)
                
            # Finally, print terminal feedback "headers" for each event within the next trial
            print(f"\n{'*'*35} Trial {self.current_trial_counter} begins {'*'*35}") # Terminal feedback...
            print(f"{'Event Type':>30} | Xcord. Ycord. | Stage | Session Time")
            
        
    #%%  Pre-choice loop 
    """
    Each MTO trial is built of four seperate stages (following the ITI). The
    AS and MTO phases each use a subset of these stages. The numeric "code" of
    each stage is given below, and are used in the "build_keys()" function 
    below to determine what keys should be colored and activated.
        
        0) Sample key loop - the sample is pecked a certain number of times. 
            This differs within the MTO phase and is fixed in the MTO. The
            AS phase only takes place within this stage.
            
        1) Delay stage - following the completion of the sample key loop, a 
            brief delay occurs in the DMTO phase. In MTO, there is no delay
            and the sample remains onscreen. 
            
        2) Choice stage - in this stage, the color of each of the parallel 
            choice keys is filled in and are activated. A single peck of either
            leads to reinforcement or 
        
        3) Feedback stage - for DMTO trials, a post-choice period featured 
            information dependent upon a subject's experimental group. For 
            experimental subjects, the sample key was illuminated with the 
            correct sample stimulus (regardless of choice). For control
            subjects, the sample key was illuminated with a grey key (e.g.,
            non-informative cue).
    """
    def ready_signal_phase(self):
        self.clear_canvas()
        self.trial_substage_start_time = time()
        self.trial_stage = 0
        self.build_keys()
        
    def ready_signal_press(self, event):
        self.write_data(event, "ready_signal_press")
        # Proceed to sample key phase...
        self.trial_substage_start_time = time()
        self.sample_key_loop(self.sample_key_FR)
    

    def sample_key_loop(self, passed_FR):
        # This is one half of the RR loop. It can be thought of as the resting
        # "return state" that is dependent upon a key press (on the O key). 
        # Otherwise, it will stay in this state forever.
        self.trial_FR = passed_FR
        self.clear_canvas()
        self.trial_stage = 1
        self.build_keys()
    
    def sample_key_press(self, event):
        # This is the other half of the RR loop. When the key is pressed in the 
        # resting state above, the function below is triggered via the
        # "build_keys()" function. If the RR is completed, then it moves
        # on to the choice phase (via the present_target() function). If not,
        # the RR is decreased by one and it returns to the resting state.
        if self.trial_stage == 1: # If sample stage
            self.write_data(event, "sample_key_press")
            if self.trial_FR <= 1:
                self.clear_canvas()
                self.build_keys()
                if self.training_phase == 1:
                    self.delay_stage()
                elif self.training_phase == 0:
                    self.matching_stage()
                    
            else:
                self.trial_FR -= 1
                self.sample_key_loop(self.trial_FR)
        else:
            self.write_data(event, "nonactive_sample_key_press")
            
    def delay_stage(self):
        self.trial_stage = 2
        self.trial_substage_start_time = time()
        self.build_keys()
        # print(f"Delay for {self.trial_delay_duration//1000} sec.")
        self.delay_timer = self.root.after(self.trial_delay_duration, self.matching_stage)
    
    def matching_stage(self):
        self.trial_stage = 3
        self.trial_substage_start_time = time()
        self.build_keys()
    
    def feedback_stage(self, correct):
        self.trial_stage = 4
        self.trial_substage_start_time = time()
        if self.stimulus_set_num == 3 and self.exp_condition == "C":
            self.feedback_duration = 1 # no feedback
        else:
            self.feedback_duration = choice(list(range(2,5))) * 1000
            self.build_keys()
        if correct:
            self.feedback_timer = self.root.after(self.feedback_duration,
                                                  lambda: self.provide_food (True))
        else: # If incorrect
            self.feedback_timer = self.root.after(self.feedback_duration,
                                                  self.time_out_func)
        
    def build_keys(self):
        # This is a function that builds the all the buttons on the Tkinter
        # Canvas. The Tkinter code (and geometry) may appear a little dense
        # here, but it follows many of the same rules. Al keys will be built
        # during non-ITI intervals, but they will only be filled in and active
        # during specific times. However, pecks to keys will be differentiated
        # regardless of activity.
        
        # First, build the background. This basically builds a button the size of 
        # screen to track any pecks; buttons built on top of this button will
        # NOT count as background pecks but as key pecks, because the object is
        # covering that part of the background. Once a peck is made, an event line
        # is appended to the data matrix.
        self.mastercanvas.create_rectangle(0,0,
                                           self.mainscreen_width,
                                           self.mainscreen_height,
                                           fill = "black",
                                           outline = "black",
                                           tag = "bkgrd")
        self.mastercanvas.tag_bind("bkgrd",
                                   "<Button-1>",
                                   lambda event, 
                                   event_type = "background_peck": 
                                       self.write_data(event, event_type))
            
            
        
        # Nest, we update all the colors needed for this stage of the trial
        self.calculate_trial_key_stimuli() # updates color list
        
                    
        key_coord_dict = {"sample_key": [300, 200, 500, 400],
                          "left_comparison_key": [55, 405, 185, 535],
                          "right_comparison_key": [615, 405, 745, 535]}
        
        # Build stimulus image, if relevant
        if self.current_key_stimulus_dict["sample_key"] not in ["white", "black", self.control_feedback_color]:
            self.mastercanvas.create_oval(key_coord_dict["sample_key"],
                                          fill = "black",
                                          outline = "black",
                                          tag = "sample_key")
            if operant_box_version:
                stimuli_folder_path = f"{str(os_path.expanduser('~'))}/OneDrive/Desktop/P034b/stimuli{self.stimulus_set_num}"
            else:
                stimuli_folder_path = f"stimuli{self.stimulus_set_num}"
                
            img = ImageTk.PhotoImage(Image.open(f"{stimuli_folder_path}/{self.current_key_stimulus_dict['sample_key']}"))
            self.mastercanvas.img = img
            self.mastercanvas.create_image(400,300, 
                                           anchor='center',
                                           image=img,
                                           tag = "sample_key")
            
            self.mastercanvas.tag_bind("sample_key",
                                       "<Button-1>",
                                       lambda event,
                                       ks = "sample_key": self.key_press(event,
                                                                    ks))
            # Remove the key from the dictionary once its built
            del key_coord_dict["sample_key"]

            
        
        # Now that we have all the coordinates linked to each specific key,
        # we can use a for loop to build each one.
        for key_string in key_coord_dict:
            # First up, build the actual circle that is the key and will
            # contain the stimulus. Order is important here, as shapes built
            # on top of each other will overlap/cover each other.
            self.mastercanvas.create_oval([key_coord_dict[key_string][0]-12.5,
                                          key_coord_dict[key_string][1]-12.5,
                                          key_coord_dict[key_string][2]+12.5,
                                          key_coord_dict[key_string][3]+12.5],
                                                         fill = "black",
                                                         outline = "black",
                                                         tag = key_string)
            
            self.mastercanvas.create_oval(key_coord_dict[key_string],
                                                       fill = self.current_key_stimulus_dict[key_string],
                                                       outline = "black",
                                                       tag = key_string)
            
            if self.current_key_stimulus_dict[key_string] == self.control_feedback_color:
                self.mastercanvas.create_rectangle([key_coord_dict[key_string][0]+30,
                                              key_coord_dict[key_string][1]+30,
                                              key_coord_dict[key_string][2]-30,
                                              key_coord_dict[key_string][3]-30],
                                                             fill = "yellow",
                                                             outline = self.control_feedback_color,
                                                             tag = key_string)
                
            self.mastercanvas.tag_bind(key_string,
                                       "<Button-1>",
                                       lambda event,
                                       key_string = key_string: self.key_press(event,
                                                                    key_string))
            
                    
        # Lastly, start an auto timer if it's autoshaping
        if self.training_phase == 2:
            self.auto_timer = self.root.after(self.auto_reinforcer_timer,
                                               lambda: self.provide_food(False)) # False b/c non autoreinforced


    def calculate_trial_key_stimuli(self):
        # This function calculates the colors for each key at a particular 
        # experimental phase and/or trial_stage. It is referenced multiple
        # times throughout each stage of a trial. It always starts by resetting
        # the color list to default
        self.current_key_stimulus_dict = {"left_comparison_key": "black",
                                       "right_comparison_key": "black",
                                       "sample_key": "black"}
        
        if self.training_phase == 2: # If autoshaping...
            for key in self.current_key_stimulus_dict:
                if key == self.illuminated_key:
                    if self.illuminated_key == "left_comparison_key":
                        self.current_key_stimulus_dict["left_comparison_key"] = self.left_comp_color
                    elif self.illuminated_key == "right_comparison_key":
                        self.current_key_stimulus_dict["right_comparison_key"] = self.right_comp_color
                    else:
                        if self.current_trial_counter > 15:
                            self.current_key_stimulus_dict["sample_key"] = choice([self.sample_stimulus, "white"])
                        else:
                            self.current_key_stimulus_dict["sample_key"] = self.sample_stimulus
                        
        elif self.trial_stage == 0:
            self.current_key_stimulus_dict["sample_key"] = "white"

        if self.trial_stage == 1 or (self.trial_stage == 3 and self.training_phase == 0): # or (self.trial_stage == 3 and self.training_phase == 1 and self.correction_procedure): # sample key
            self.current_key_stimulus_dict["sample_key"] = self.sample_stimulus
            
        if self.trial_stage == 3 and self.training_phase != 3: # works for DMTO and MTO
            self.current_key_stimulus_dict["left_comparison_key"] = self.left_comp_color
            self.current_key_stimulus_dict["right_comparison_key"] = self.right_comp_color
        
# =============================================================================
#         elif self.trial_stage == 2 and self.training_phase == 3 and not self.correction_procedure: # works for forced choice
#             left_or_right = choice(["left_comparison_key", "right_comparison_key"])
#             print(left_or_right)
#             self.current_key_stimulus_dict[left_or_right] = self.sample_stimulus
# =============================================================================
            
        elif self.trial_stage == 4: # only works for DMTO
            if self.exp_condition == 'E':
                self.current_key_stimulus_dict["sample_key"] = self.sample_stimulus
             # For the control condition...
            elif self.stimulus_set_num > 1:
                self.current_key_stimulus_dict["sample_key"] = self.feedback_stimulus
            else:
                self.current_key_stimulus_dict["sample_key"] = self.control_feedback_color

    
    """ 
    The three functions below represent the outcomes of choices made under the 
    two different cotnigencies (simple or choice). In the simple task (with
    only one "choice" key and target color), any response on the green "choice" 
    key within time contraints is correct and will be reinforced and logged as
    such. In the true choice task, only a choice of the "correct" target-color
    matching key will be reinforced; the opposite key leads to a TO.
    
    Note that, in this setup, the left and right choice keys are fixed to a 
    specific color (left is always blue). We'll need to counterbalance color
    across subjects later on.
    """
    
    def key_press(self, event, keytag):
        # First, make sure the keys are actually active

        if self.current_key_stimulus_dict[keytag] == "black":
            self.write_data(event, (f"non_active_{keytag}_peck"))
            
        elif self.training_phase == 2: # If autoshaping
            self.write_data(event, (f"auto_shaping_active_{keytag}_peck"))
            # Next, cancel the timer (if it exists)
            try:
                self.root.after_cancel(self.auto_timer)
            except AttributeError:
                pass
            self.provide_food(True)
            
        elif self.current_key_stimulus_dict[keytag] == "white":
            self.ready_signal_press(event)
            
        else:
            if keytag == "sample_key": # For sample key, offload to different function
                self.sample_key_press(event)
            else: # For choice keys...
                if self.trial_stage == 3: 
                    # If correct choice
                    if (self.current_key_stimulus_dict[keytag] == "red" and self.correct_key == "R") or (self.current_key_stimulus_dict[keytag] == "green" and self.correct_key == "L"):
                        self.write_data(event, "correct_choice")
                        if self.training_phase == 1: #and not self.correction_procedure:
                            self.feedback_stage(True)
                        else:
                            self.provide_food(True) 
                     # If incorrect choice...
                    else:
                        self.write_data(event, "incorrect_choice")
                        if self.training_phase == 1: #and not self.correction_procedure:
                            self.feedback_stage(False)
                        else:
                            self.time_out_func()
                
                else: # If choice stage (e.g., keys aren't active)
                    self.write_data(event, (f"non_active_{keytag}_peck"))
        
    
    # %% Post-choice contingencies: always either reinforcement (provide_food)
    # or time-out (time_out_func). Both lead back to the next trial's ITI,
    # thereby completing the loop.
    
    def provide_food(self, key_pecked):
        # This function is contingent upon correct and timely choice key
        # response. It opens the hopper and then leads to ITI after a preset
        # reinforcement interval (i.e., hopper down duration)
        self.clear_canvas()
        self.write_data(None, "reinforcer_provided")
        
        # We first need to add one to the non-CP counter
        self.non_CP_trials += 1
        self.previous_trial_correct = True
        
        # If key is operantly reinforced
        if key_pecked:
            if not operant_box_version or self.subject_ID == "TEST":
                self.mastercanvas.create_text(400,300,
                                              fill="white",
                                              font="Times 20 italic bold", 
                                              text=f"Correct Key Pecked \nFood accessible ({int(self.hopper_duration/1000)} s)") # just onscreen feedback
        else: # If auto-reinforced
            if not operant_box_version or self.subject_ID == "TEST":
                    self.mastercanvas.create_text(400,300,
                                  fill="White",
                                  font="Times 20 italic bold", 
                                  text=f"Auto-timer complete \nFood accessible ({int(self.hopper_duration/1000)} s)") # just onscreen feedback
            self.write_data(None, "auto_reinforcer_provided")
        if operant_box_version:
            self.Hopper.change_hopper_state("On") # turn on hopper
        self.root.after(self.hopper_duration, lambda: self.ITI())

    def time_out_func(self):
        # TO occurs after INCORRECT choice or no response. It also leads back to 
        # the ITI interval, but after a longer period of time (TO).
        self.write_data(None, "time_out")
        self.clear_canvas()
        
        # Make sure pecks during timeout are saved
        self.mastercanvas.create_rectangle(0,0,
                                           self.mainscreen_width,
                                           self.mainscreen_height,
                                           fill = "black",
                                           outline = "black",
                                           tag = "bkgrd")
        self.mastercanvas.tag_bind("bkgrd",
                                   "<Button-1>",
                                   lambda event, 
                                   event_type = "TO_peck": 
                                       self.write_data(event, event_type))
            
        # Next, for correction procedure
        self.previous_trial_correct = False
        #if not self.correction_procedure:
        self.non_CP_trials += 1 
        if not operant_box_version or self.subject_ID == "TEST":
            self.mastercanvas.create_text(400,300,fill="white",font="Times 20 italic bold",
                                text="Time out (%ds)" % (self.TO_duration/1000))
        self.root.after(self.TO_duration, lambda: self.ITI())
        

    # %% Outside of the main loop functions, there are several additional
    # repeated functions that are called either outside of the loop or 
    # multiple times across phases.
    
    def change_cursor_state(self):
        # This function toggles the cursor state on/off. 
        # May need to update accessibility settings on your machince.
        if self.cursor_visible: # If cursor currently on...
            self.root.config(cursor="none") # Turn off cursor
            print("### Cursor turned off ###")
            self.cursor_visible = False
        else: # If cursor currently off...
            self.root.config(cursor="") # Turn on cursor
            print("### Cursor turned on ###")
            self.cursor_visible = True
    
    def clear_canvas(self):
         # This is by far the most called function across the program. It
         # deletes all the objects currently on the Canvas. A finer point to 
         # note here is that objects still exist onscreen if they are covered
         # up (rendering them invisible and inaccessible); if too many objects
         # are stacked upon each other, it can may be too difficult to track/
         # project at once (especially if many of the objects have functions 
         # tied to them. Therefore, its important to frequently clean up the 
         # Canvas by literally deleting every element.
        try:
            self.mastercanvas.delete("all")
        except TclError:
            print("No screen to exit")
        
    def exit_program(self, event): 
        # This function can be called two different ways: automatically (when
        # time/reinforcer session constraints are reached) or manually (via the
        # "End Program" button in the control panel or bound "esc" key).
            
        # The program does a few different things:
        #   1) Return hopper to down state, in case session was manually ended
        #       during reinforcement (it shouldn't be)
        #   2) Turn cursor back on
        #   3) Writes compiled data matrix to a .csv file 
        #   4) Destroys the Canvas object 
        #   5) Calls the Paint object, which creates an onscreen Paint Canvas.
        #       In the future, if we aren't using the paint object, we'll need 
        #       to 
        def other_exit_funcs():
            if operant_box_version:
                self.Hopper.change_hopper_state("Off")
                # root.after_cancel(AFTER)
                if not self.cursor_visible:
                	self.change_cursor_state() # turn cursor back on, if applicable
            self.write_comp_data(True) # write data for end of session
            self.root.destroy() # destroy Canvas
            print("\n GUI window exited")
            
        self.clear_canvas()
        other_exit_funcs()
        print("\n You may now exit the terminal and operater windows now.")
        if operant_box_version:
            polygon_fill.main(self.subject_ID) # call paint object
        
    
    def write_data(self, event, outcome):
        # This function writes a new data line after EVERY peck. Data is
        # organized into a matrix (just a list/vector with two dimensions,
        # similar to a table). This matrix is appended to throughout the 
        # session, then written to a .csv once at the end of the session.
        if event != None: 
            x, y = event.x, event.y
        else: # There are certain data events that are not pecks.
            x, y = "NA", "NA"   
            
# =============================================================================
#         if self.previous_trial_correct and self.correction_procedure:
#             correction_trial = 0
#         elif self.correction_procedure:
#             correction_trial = 1
#         else:
# =============================================================================
        correction_trial = "NA"
            
        print(f"{outcome:>30} | x: {x: ^3} y: {y:^3} | {self.trial_stage:^5} | {str(datetime.now() - self.start_time)}")
        # print(f"{outcome:>30} | x: {x: ^3} y: {y:^3} | Target: {self.current_target_location: ^2} | {str(datetime.now() - self.start_time)}")
        self.session_data_frame.append([
            str(datetime.now() - self.start_time), # SessionTime as datetime object
            x, # X coordinate of a peck
            y, # Y coordinate of a peck
            outcome, # Type of event (e.g., background peck, target presentation, session end, etc.)
            correction_trial, # 1/0 boolean for correction procedure
            self.sample_stimulus.split(".")[0], # Name of sample (w/o ".png)
            self.correct_key, # Correct choice
            self.exp_condition, # control or experimental condition
            self.trial_stage, # Substage within each trial (1-4 for DMTO)
            round((time() - self.trial_start - (self.ITI_duration/1000)), 5), # Time into this trial minus ITI (if session ends during ITI, will be negative)
            round((time() - self.trial_substage_start_time), 5), # Trial substage timer
            self.current_trial_counter, # Trial count within session (1 - max # trials)
            self.non_CP_trials, # Non-correction procedure trial counter
            self.trial_delay_duration, # Duration of a delay (in seconds)
            self.feedback_duration, # Duration of the feedback (in ms)
            self.trial_FR, # FR of a specific trial
            self.subject_ID, # Name of subject (same across datasheet)
            self.exp_condition, # Condition
            self.training_phase, # Phase of training as a number 0-2
            self.stimulus_set_num,
            date.today() # Today's date as "MM-DD-YYYY"
            ])
        
        header_list = ["SessionTime", "Xcord","Ycord", "Event",
                       "CorrectionTrial", "SampleStimulus", "CorrectKey",
                       "StimulusCondition", "TrialSubStage", "TrialTime", 
                       "TrialSubStageTimer","TrialNum", "NonCPTrialNum",
                       "DelayDuration", "FeedbackDuration", "SampleFR",
                       "Subject", "ExpCondition", "TrainingPhase",
                       "StimulusSetNum", "Date"] # Column headers

        
    def write_comp_data(self, SessionEnded):
        # The following function creates a .csv data document. It is either 
        # called after each trial during the ITI (SessionEnded ==False) or 
        # one the session finishes (SessionEnded). If the first time the 
        # function is called, it will produce a new .csv out of the
        # session_data_matrix variable, named after the subject, date, and
        # training phase. Consecutive iterations of the function will simply
        # write over the existing document.
        if SessionEnded:
            self.write_data(None, "SessionEnds") # Writes end of session to df
        if self.record_data : # If experimenter has choosen to automatically record data in seperate sheet:
            myFile_loc = f"{self.data_folder_directory}/{self.subject_ID}/{self.subject_ID}_{self.start_time.strftime('%Y-%m-%d_%H.%M.%S')}_P034b_data-Phase{self.training_phase}.csv" # location of written .csv
            # This loop writes the data in the matrix to the .csv              
            edit_myFile = open(myFile_loc, 'w', newline='')
            with edit_myFile as myFile:
                w = writer(myFile, quoting=QUOTE_MINIMAL)
                w.writerows(self.session_data_frame) # Write all event/trial data 
            print(f"\n- Data file written to {myFile_loc}")
                
#%% Finally, this is the code that actually runs:
    
if __name__ == '__main__':
    cp = ExperimenterControlPanel()


    
