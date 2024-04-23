document.addEventListener("DOMContentLoaded", function() {
    var revealButton = document.getElementById("reveal-button");
    var numberContainer = document.getElementById("number-container");

    revealButton.addEventListener("click", function() {
        if (numberContainer.classList.contains('visible')) {
            numberContainer.classList.remove('visible');
            numberContainer.style.visibility = 'hidden';
            numberContainer.style.opacity = '0';
            revealButton.textContent = "Reveal Number";
        } else {
            numberContainer.classList.add('visible');
            numberContainer.style.visibility = 'visible';
            numberContainer.style.opacity = '1';
            numberContainer.textContent = "Not yet live - check back later!";
            revealButton.textContent = "Hide Number";
        }
    });
});
