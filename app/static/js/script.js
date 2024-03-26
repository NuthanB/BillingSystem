function logout() {
  // Perform logout actions here, such as redirecting to logout route or clearing session
  // For example:
  fetch("/logout", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({}),
  })
    .then((response) => {
      if (response.ok) {
        // Handle successful logout
        console.log("Logged out successfully");
        // Redirect to login page or perform any other necessary action
        window.location.href = "/login";
      } else {
        // Handle error response
        console.error("Failed to logout:", response.statusText);
      }
    })
    .catch((error) => {
      // Handle network error
      console.error("Error logging out:", error);
    });
}
