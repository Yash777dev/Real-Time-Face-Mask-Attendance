// admin.js — Admin directory search, AJAX deletion, and CSV report export

document.addEventListener('DOMContentLoaded', () => {
    // Student deletion AJAX
    document.querySelectorAll('.delete-student-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const studentId = btn.dataset.studentId;
            const studentName = btn.dataset.studentName;

            confirmAction(
                'Delete Student',
                `Are you sure you want to delete ${studentName}? All associated face images and attendance records will be removed.`,
                async () => {
                    try {
                        const data = await apiFetch(`/api/delete-student/${studentId}`, {
                            method: 'DELETE'
                        });

                        if (data.success) {
                            Toast.success(data.message);
                            btn.closest('tr').remove();
                        } else {
                            Toast.error(data.message || 'Deletion failed');
                        }
                    } catch (err) {
                        Toast.error('Error deleting student: ' + err.message);
                    }
                },
                'Delete',
                'btn-outline'
            );
        });
    });

    // CSV Export button handler
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', async () => {
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            const dept = document.getElementById('exportDept').value;

            if (!startDate || !endDate) {
                Toast.warning('Please select start and end dates');
                return;
            }

            exportBtn.disabled = true;
            exportBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating CSV...';

            try {
                const response = await fetch('/api/export-attendance', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        start_date: startDate,
                        end_date: endDate,
                        department: dept
                    })
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `attendance_report_${startDate}_to_${endDate}.csv`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                    Toast.success('CSV Report downloaded');
                } else {
                    Toast.error('Failed to export CSV report');
                }
            } catch (err) {
                Toast.error('Export error: ' + err.message);
            } finally {
                exportBtn.disabled = false;
                exportBtn.innerHTML = '<i class="fa-solid fa-download"></i> Download CSV Report';
            }
        });
    }
});
