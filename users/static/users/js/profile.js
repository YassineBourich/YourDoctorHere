const prof_edit_btn = document.querySelector('#prof_edit_btn'),
pass_change_btn = document.querySelector('#pass_change_btn'),
acc_del_btn = document.querySelector('#acc_del_btn');

const extention = document.querySelector("#extention").value;

prof_edit_btn.onclick = (e) => {
    e.preventDefault();
    window.location.href = "/" + extention + "/edit/";
}

pass_change_btn.onclick = (e) => {
    e.preventDefault();
    window.location.href = "/" + extention + "/change-password/";
}

acc_del_btn.onclick = (e) => {
    e.preventDefault();
    window.location.href = "/" + extention + "/delete/";
}