// Function to handle radio button toggling
function toggleRadio(radio) {
  if (radio._clicked) {
    radio.checked = false;
    radio._clicked = false;
  } else {
    radio._clicked = true;
  }
}

// Initialize and add event listeners when the page loads
document.addEventListener('htmx:load', function(event) {
  const radios = event.detail.elt.querySelectorAll('.toggleable-radio');
  
  // Initialize the state for all radio buttons
  radios.forEach(radio => {
    radio._clicked = radio.checked;
    
    // Add click event listener
    radio.addEventListener('click', function() {
      toggleRadio(this);
    });
  });
});