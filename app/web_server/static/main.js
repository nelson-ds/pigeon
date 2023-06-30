document.addEventListener("DOMContentLoaded", function() {
    var dynamicContent = document.getElementById("pet-action");
    var updateButton = document.getElementById("pet-button");
    var clickCount = 0;

    updateButton.addEventListener("click", function() {
        clickCount++;
        var newParagraph = document.createElement("p");
        newParagraph.textContent = ' coo'.repeat(clickCount);
        dynamicContent.appendChild(newParagraph);
    });
});