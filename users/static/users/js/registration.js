const patientBtn = document.querySelector("#patient-btn");
const doctorBtn = document.querySelector("#doctor-btn");
const patientForm = document.querySelector('[data-entity-form="patient"]');
const doctorForm = document.querySelector('[data-entity-form="doctor"]');

function switchEntity(entityType) {
    if (!patientForm || !doctorForm) {
        return;
    }

    patientForm.hidden = entityType !== "patient";
    doctorForm.hidden = entityType !== "doctor";
}

if (patientBtn) {
    patientBtn.onclick = () => switchEntity("patient");
}

if (doctorBtn) {
    doctorBtn.onclick = () => switchEntity("doctor");
}
