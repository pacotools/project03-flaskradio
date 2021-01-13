$(document).ready(function(){
    $(".sidenav").sidenav({edge: "right"});
    $('.collapsible').collapsible();
    $('select').formSelect();
});

// Play a station clicked with play button
//function playStation () {
function playStation (url_resolved) {
    sound = new Howl({
        src: url_resolved,
        html5: true,
        format: ['webm'],
    });
    sound.load();
    sound.play();
}

function stopStation () {
    if (sound.playing()) {
        sound.unload();
    }
}

function force_submit (form) {
    document.getElementById(form).click();
}