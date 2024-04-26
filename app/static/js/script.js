function logout() {
  fetch("/logout", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({}),
  })
    .then((response) => {
      if (response.ok) {
        window.location.href = "/login";
      } else {
        console.error("Failed to logout:", response.statusText);
      }
    })
    .catch((error) => {
      console.error("Error logging out:", error);
    });
}

const modal = document.querySelector(".modal");
const overlay = document.querySelector(".overlay");

const closeModal = function () {
  modal.classList.add("hidden");
  overlay.classList.add("hidden");
  window.location.reload();
};

document.addEventListener("keydown", function (e) {
  if (e.key === "Enter" && !modal.classList.contains("hidden")) {
    closeModal();
  }
});

const openModal = function (message) {
  document.getElementById("errmsg").textContent = message;
  modal.classList.remove("hidden");
  overlay.classList.remove("hidden");
};
