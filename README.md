# groupify

**Proposed Level of Achievement:** Apollo 11


Groupify is a telegram bot that contains several features that would be useful to groups who want to organise meet ups, such as a Meet-up Scheduler, a Bill Splitter and an Event Organiser.


**Motivation**

In many friend groups such as our own, we often encounter situations where we want to meet up sometime soon but have no idea what would be a good time. Typically, someone suggests a time to meet up, and then various members of the group reply over the next few hours, only for one person to reply that he cannot make it, thus causing the whole plan to fall apart. Even if the group comes to a consensus, usually the message history is flooded and there is no easy way to retrieve the outcome.

There exist certain websites that allow users to put in the times when they are available, but they can be rather inconvenient for users as someone usually has to create some event and get everyone to click on a link for an external site. The UI might also not be ideal for mobile platforms.

Furthermore, another common issue that we notice in group outings is having to split the bill after meals. Oftentimes, it can be a bother trying to calculate the exact cost that each person should pay, especially when you take into account the GST and Service Charge. Also, the group is usually busy talking and the person who paid has to calculate everything in their own time, message the group, and then make sure that everyone has remembered to pay. It can be quite a stressful experience having to chase down friends who might have procrastinated paying and just forgotten.

Thus, we see an opportunity to create a bot that can tackle these issues while also being integrated into the messaging app and being convenient and easy to use.


**Aim**

Planning should not be a burden - one should look forward to planning activities to meet up with their close ones and have fun. Our product aims to make it easier for groups, be it friends or families, to be able to easily plan their activities, and make the execution of the activity not a chore. After chatting on a messaging platform to make plans for an activity, our product will enable them to easily upload the finalized information onto it. The bot will then provide the users valuable information to organize the time and place of their activity, as well as provide additional quality-of-life features to make going-out less of a hassle. 

Ultimately, it is aimed to be an all-in-one bot that handles the menial pre-planning and post-consolidatory tasks of hanging out. We strive to put the fun back in a fun night out.




**User Stories**


1. As a user, I want to be able to easily come to an agreement on when to meet with my friends, such that everyone is able to make it. It should allow everyone to fill in their open time slots in a convenient manner, reducing back-and-forth discussions.

2. As a user who lives far away from all of my friends in my friend group, I want to be able to identify the best centralized location for all of us to meet at, for any particular type of activity.

3. As a user who is very nit picky when it comes to money, I would like to quickly split the bill amongst my group at the end of the day, and keep track of who owes what without having to chase them for it.

4. As a user, I want to be able to quickly build a list that has the finalized activities for the day sorted by time, so that everyone in the group is on the same page on the day itself.


**Core Features**


The Telegram Bot provides several commands that users can use to launch one of the following three core functions:
Meet-up Scheduler
Bill Splitter
Event Organiser


**Meet-up Scheduler Features:**

The main purpose of the meet-up scheduler is to derive a common optimum time amongst all users, for the event to be held at. 
It also has a secondary optional feature, a Location Suggester. The Location Suggester will choose the optimum place for the users to have a particular type of event at (e.g. nearest restaurant or library between all users).

a) Start new event by a user
  - Bot will prompt user for title, short description, minimum time, timeframe for event (next week, next 2 weeks), and participants
  - Bot will prompt user whether they require a Location Suggester. If the feature is chosen, the bot will further prompt user to choose a type of venue (e.g. food place, movie     theatre, park, MRT, etc.)
b) Fill timeslots - users will have a UI pop up, possibly made with HTML, to display a time table, allowing users to select which days and times they are free
c) If Location Suggester is enabled, users will need to input their starting location for the event.
d) Auto result calculation - after all users in the group have filled up their time slots, the bot will message the group with the optimal time where the most people can attend
  - Users can choose to accept the proposed time slot, or choose another one
  -  After confirmation, user can select whether to receive reminders 
  -  Time slot of event can still be changed
  -  Should Location Suggester be enabled, the message from the bot will include the calculated optimum location, such that it is as close as possible to all users.
     Event creator can opt for a recalculation of the location for a different suggestion.
e) View results - users should still be able to view the full calendar, and change their time slots
f) Reminder - bot will message reminders to the group before the event




**Bill Splitter Features:**

The Bill Splitter has different functionalities for the host (person who pays the total bill and is now attempting to collect the owed money) and the other users.

Host:
a) Create new bill and select users in the chat group who are responsible for the bill
b) Upload image of receipt for evidence. 
c) Insert items in receipt into a UI.
d) Select users from the bill group who are responsible for each item.
e) Fill in GST and Service charge, allowing bot to calculate payment
f) Update any of the above details.
g) Disable payment reminders for the users.
h) Finalize bill before sending auto-customized payment breakdown to each user.
i) Checklist for host to indicate people who have already paid

User:
a) View personalized bill statement, which contains the total sum that the person needs to pay the host, along with the breakdown of how the total sum is derived
b) Reminders to pay the bill - can be configured to choose how frequently to remind, with a maximum time limit of 24 hours between each reminder. Reminders cannot be toggled to be entirely turned off by the user, unless the Host wishes to do so.




**Event Organiser Features**

The Event Organiser enables people to insert finalized events into a common list. The bot will auto-sort the items by chronological order. The features are as follows;

a) Start new event by a user
b) Bot will prompt user to choose a name for the event and select participants for the event. A main list will be created, with no current sub-events.
c) Any user will be able to create a sub-event, and input parameters for time, place, and activity, which will be proposed to the group.
d) If all users approve the sub-event, the event will be added to the main list.
e) The list will auto sort in chronological order and be posted to the group.
f) Any user can retrieve the main-list at any time.


**Project Scope & Timeline**

Objectives completed thus far:



Features to be completed by end June:
Finish up most features for the Bill Splitter
Finish up basic feature for Event Scheduler
Create prototype for timetable program to be used in Event Scheduler and test it
Test auto-suggester and figure out best way to decide time slots
Implement Event Organiser if time permits

Features to be completed by the mid-end of July: 

Polish up features, fully integrate all the features for Bill Splitter and Event Scheduler
Test the bot and ensure it is working as intended
Possibly add additional features that would be suited to the purpose of the bot
Integrate Google Pay to Bill Splitter?

![image](https://user-images.githubusercontent.com/13115675/120102136-31c48400-c17c-11eb-8ea5-a1f36151986e.png)
