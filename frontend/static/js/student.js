// student.js — Student dashboard async attendance percentage loader

document.addEventListener('DOMContentLoaded', () => {
    loadAttendancePercentage();
});

async function loadAttendancePercentage() {
    const el = document.getElementById('attendancePercentage');
    if (!el) return;

    try {
        const data = await apiFetch('/student/api/attendance-percentage');
        if (data.success) {
            animateNumber(el, data.percentage || 0);
            el.textContent = `${data.percentage}%`;
        }
    } catch (err) {
        console.error('Error loading attendance percentage:', err);
        el.textContent = 'N/A';
    }
}
