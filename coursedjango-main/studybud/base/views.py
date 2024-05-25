from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
#restrict not login user from specific function
from django.contrib.auth.decorators import login_required



# Create your views here.
# rooms = [
#     {'id':1, 'name':'Lets learn python'},
#     {'id':2, 'name':'Design with me'},
#     {'id':3, 'name':'Frontend Developer'},
# ]

def loginPage(request):
    #to let the template know what page is this by using if else
    page = 'login'

    #restricted user from relogin
    if request.user.is_authenticated:
        messages.error(request,'You have logged in')
        return redirect('home')
        

    if request.method == "POST":
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        #Check if user exist
        try:
            username = User.objects.get(email=email)
        except:
            messages.error(request, 'User does not exist')
        #use authenticate
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username or Password is incorrect')

    context = {'page': page}
    return render(request, 'base/login_register.html', context)

def logoutUser(request):
    logout(request)
    return redirect('home')

def registerPage(request):
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            #after user was created, want to access (clean the data) the user right way, use commit false
            user = form.save(commit=False)
            #clean the data
            user.username = user.username.lower()
            user.save()
            #after registration, login the user
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occured during registration')

    context = {'form':form}
    return render(request, 'base/login_register.html', context)

def home(request):
    #filter function
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    # import Q give you the ability to use (and, or)
    rooms = Room.objects.filter(
        #you cant use host to search because of foreignkey, must through parent class
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q) |
        Q(host__username__icontains=q)
        )
    #get topics
    topics = Topic.objects.all()[0:5]
    #count rooms
    room_count = rooms.count()
    #get activity feed
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))[0:5]
    context = {'rooms':rooms, 'topics': topics, 'room_count':room_count, 'room_messages': room_messages}
    return render(request, 'base/home.html', context)

def room(request, pk):
    room = Room.objects.get(id = pk)
    #get messages from the model Message but using instead of M, we use m
    #give me all the messages related to this room by get to its child
    room_messages = room.message_set.all()
    #get participants
    participants = room.participants.all()
    #user write message
    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,
            room = room,
            #get the body through name of the input
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    context = {'room': room, 'room_messages': room_messages, 'participants':participants}
    return render(request, 'base/room.html', context)

def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user': user, 'rooms': rooms, 'room_messages': room_messages, 'topics': topics}
    return render(request, 'base/profile.html', context)

@login_required(login_url='/login')
def createRoom(request):
    form  = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description')
        )
        return redirect('home')
    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html',context)

@login_required(login_url='/login')
def updateRoom(request, pk):
    #prefill form
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    #Authorize if the user is the host of the room
    if request.user != room.host:
        return HttpResponse('Your are not allowed that!!')

    #update data, like create one's
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get("description")
        room.save()
        return redirect('home')
    context = {'form': form, 'topics': topics, 'room': room}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='/login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    #Authorize if the user is the host of the room
    if request.user != room.host:
        return HttpResponse('Your are not allowed to do that!!')

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': room})

@login_required(login_url='/login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)
    #Authorize if the user is the host of the room
    if request.user != message.user:
        return HttpResponse('Your are not allowed to do that!!')

    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': message})

@login_required(login_url='/login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)

    context = {'form': form}
    return render(request, 'base/update-user.html', context)

def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(Q(name__icontains=q))
    return render(request, 'base/topics.html', {'topics': topics})

def activitiesPage(request):
    room_messages = Message.objects.all()
    context = {'room_messages': room_messages}
    return render(request, 'base/activity.html', context)