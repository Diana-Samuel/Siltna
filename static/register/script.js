function toggleSignup() {
    document.querySelector(".form-toggle").classList.add("active");
    document.getElementById("signup-toggle").classList.add("active-btn");
    document.getElementById("login-toggle").classList.remove("active-btn");
    document.getElementById("login-form").style.display = "none";
    document.getElementById("signup-form").style.display = "block";
}

function toggleLogin() {
    document.querySelector(".form-toggle").classList.remove("active");
    document.getElementById("login-toggle").classList.add("active-btn");
    document.getElementById("signup-toggle").classList.remove("active-btn");
    document.getElementById("signup-form").style.display = "none";
    document.getElementById("login-form").style.display = "block";
}

