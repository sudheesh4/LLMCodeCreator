// get the container element
const container = document.querySelector(".container");
// get the gallery ul element
const gallery = document.getElementById("gallery");
// set a maximum height for the container
container.style.maxHeight = "500px";
// add an event listener to the scroll wheel or touch
container.addEventListener("wheel", () => {
  // calculate the current scroll position
  const scrollPosition = container.scrollTop;
  // update the gallery's left property based on the scroll position
  gallery.style.transform = `translateX(${scrollPosition}px)`;
});
