document.addEventListener("DOMContentLoaded", () => {
  if (localStorage.getItem("theme") === "dark") {
    document.body.classList.add("dark-theme");
    document.getElementById("theme-icon").classList.replace("fa-moon", "fa-sun");
  }
});

function toggleTheme() {
  document.body.classList.toggle("dark-theme");
  const icon = document.getElementById("theme-icon");
  if (document.body.classList.contains("dark-theme")) {
    localStorage.setItem("theme", "dark");
    icon.classList.replace("fa-moon", "fa-sun");
  } else {
    localStorage.setItem("theme", "light");
    icon.classList.replace("fa-sun", "fa-moon");
  }
}