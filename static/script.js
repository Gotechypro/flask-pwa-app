let reminderInterval;
let reminderActive = false;


const reminderSound = new Audio('/static/ab.mp3'); 

document.getElementById('startReminder').addEventListener('click', function() {
    if (!reminderActive) {
        reminderActive = true;
        fetch('/start_reminder')
            .then(response => response.json())
            .then(data => {
                document.getElementById('status').innerText = 'Status: Active';
                startReminder();
            })
            .catch(error => console.error('Error:', error));
    }
});

document.getElementById('stopReminder').addEventListener('click', function() {
    if (reminderActive) {
        reminderActive = false;
        fetch('/stop_reminder') 
            .then(response => response.json())
            .then(data => {
                document.getElementById('status').innerText = 'Status: Inactive';
                clearInterval(reminderInterval); 
            })
            .catch(error => console.error('Error:', error));
    }
});

function startReminder() {
    reminderInterval = setInterval(() => {
       
        reminderSound.play().catch(error => {
            console.error('Sound playback error:', error);
        });

       
        alert("Please look outside");
    }, 60000); 
}
