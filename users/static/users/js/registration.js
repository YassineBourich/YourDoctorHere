const patient_btn = document.querySelector("#patient-btn"),
doctor_btn = document.querySelector("#doctor-btn"),
hospital_btn = document.querySelector("#hospital-btn");

const PATIENT = "PATIENT",
DOCTOR = "DOCTOR",
HOSPITAL = "HOSPITAL";

function switch_entity(event, entity_type) {
    event.preventDefault();
    console.log("fiuvgdskfvg");
}

patient_btn.onclick = (e) => {
    switch_entity(e, PATIENT);
}

doctor_btn.onclick = (e) => {
    switch_entity(e, DOCTOR);
}

hospital_btn.onclick = (e) => {
    switch_entity(e, HOSPITAL);
}