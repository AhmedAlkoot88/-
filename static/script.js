let searchTimeout;
let printSelection = 'all';

// ✅ عرض التبويب المختار
function showTab(tabName, btn) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.remove('active');
    });
    
    const tabElement = document.getElementById(tabName + '-tab');
    if (tabElement) {
        tabElement.classList.add('active');
        btn.classList.add('active');
        
        if (tabName === 'alert') {
            updateAlertsTable();
        }
    }
}

// ✅ عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('alert-table')) {
        updateAlertsTable();
    }
    
    const searchInput = document.getElementById('search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(searchItems, 300);
        });
    }
    
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-btn')) {
            e.preventDefault();
            const itemId = e.target.getAttribute('data-id');
            if (itemId) {
                deleteItem(itemId);
            }
        }
    });

    if (document.getElementById('allTable')) {
        setupAdvancedExport();
    }
});

// ✅ البحث
function searchItems() {
    const searchInput = document.getElementById('search');
    if (!searchInput) return;
    
    const query = searchInput.value.toLowerCase().trim();
    const rows = document.querySelectorAll('#allTable tr:not(:first-child)');
    let count = 0;
    
    rows.forEach(row => {
        if (row.cells.length >= 2) {
            const name = row.cells[0].textContent.toLowerCase();
            const carton = row.cells[1].textContent.toLowerCase();
            
            if (name.includes(query) || carton.includes(query) || query === '') {
                row.style.display = '';
                count++;
            } else {
                row.style.display = 'none';
            }
        }
    });
    
    const countElement = document.getElementById('count');
    if (countElement) {
        countElement.textContent = count > 0 ? `(${count} نتيجة)` : '';
    }
}

// ✅ حذف صنف
function deleteItem(itemId) {
    if (!itemId) {
        alert('❌ خطأ في تعريف الصنف');
        return;
    }
    
    if (confirm('هل أنت متأكد من حذف هذا الصنف؟ هذا الإجراء لا يمكن التراجع عنه!')) {
        fetch(`/delete_item/${itemId}`, { 
            method: 'POST',
            headers: { 
                'X-Requested-With': 'XMLHttpRequest', 
                'Content-Type': 'application/json' 
            }
        })
        .then(response => {
            if (!response.ok) throw new Error('خطأ في الرد');
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const row = document.querySelector(`[data-id="${itemId}"]`)?.closest('tr');
                if (row) {
                    row.style.opacity = '0.5';
                    setTimeout(() => row.remove(), 300);
                }
                updateAlertsTable();
                alert('✅ تم الحذف بنجاح');
                location.reload();
            } else {
                alert('❌ خطأ: ' + (data.message || 'غير معروف'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('❌ خطأ في الاتصال بالخادم');
        });
    }
}

// ✅ تحديث جدول التنبيهات
function updateAlertsTable() {
    const table = document.getElementById('alert-table');
    if (!table) return;
    
    while (table.rows.length > 1) {
        table.deleteRow(1);
    }
    
    const alertRows = document.querySelectorAll('#allTable tr.low, #allTable tr.zero');
    
    if (alertRows.length === 0) {
        const row = table.insertRow();
        const cell = row.insertCell();
        cell.colSpan = 8;
        cell.textContent = 'لا توجد تنبيهات ✅';
        cell.style.cssText = 'text-align:center;padding:20px;color:#4caf50;font-weight:bold;';
        return;
    }
    
    alertRows.forEach((row, index) => {
        const newRow = table.insertRow();
        newRow.className = row.className;
        newRow.setAttribute('data-id', row.getAttribute('data-id') || '');
        
        const serialCell = newRow.insertCell();
        serialCell.textContent = index + 1;
        serialCell.style.cssText = 'font-weight:bold;color:#4fc3f7;';
        
        for (let i = 0; i < 5 && i < row.cells.length; i++) {
            const cell = newRow.insertCell();
            cell.textContent = row.cells[i].textContent;
        }
        
        const statusCell = newRow.insertCell();
        if (row.classList.contains('zero')) {
            statusCell.textContent = '🔴 نفد المخزون';
            statusCell.style.color = '#f44336';
        } else {
            statusCell.textContent = '🟠 قليل المخزون';
            statusCell.style.color = '#ff9800';
        }
        statusCell.style.fontWeight = 'bold';
        
        const actionCell = newRow.insertCell();
        if (row.cells[row.cells.length - 1]) {
            actionCell.innerHTML = row.cells[row.cells.length - 1].innerHTML;
        }
    });
}

// ✅ خصم الكمية
function deductQuantity(itemId, cartons) {
    if (!itemId || cartons <= 0) {
        alert('❌ بيانات غير صحيحة');
        return;
    }
    
    fetch(`/deduct/${itemId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cartons: parseInt(cartons) })
    })
    .then(response => {
        if (!response.ok) throw new Error('خطأ في الرد');
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert(`✅ تم خصم ${cartons} كرتونة\nالكمية الجديدة: ${data.new_quantity}`);
            location.reload();
        } else {
            alert('❌ ' + (data.message || 'حدث خطأ'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('❌ خطأ في الاتصال بالخادم');
    });
}

// ✅ نظام التصدير
function setupAdvancedExport() {
    const header = document.querySelector('.header');
    if (!header) return;
    
    if (document.getElementById('export-modal')) return;
    
    createExportModal();
}

// ✅ إنشاء المودال
function createExportModal() {
    const modal = document.createElement('div');
    modal.id = 'export-modal';
    modal.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100vh;
        background: rgba(15,15,35,0.98); backdrop-filter: blur(30px); z-index: 10001; 
        display: none; align-items: center; justify-content: center; padding: 20px;
    `;
    
    modal.innerHTML = `
        <div class="export-modal-content">
            <div class="modal-header">
                <div class="modal-icon">📊</div>
                <h2>خيارات التصدير المتقدم</h2>
                <button class="modal-close">×</button>
            </div>
            <div class="export-grid">
                <div class="export-card" data-type="all" data-excel="false">
                    <div class="card-icon">🖨️</div>
                    <h3>طباعة كاملة</h3>
                    <p>جميع الأصناف <span class="count-badge" id="print-all-count">0</span></p>
                </div>
                <div class="export-card" data-type="alerts" data-excel="false">
                    <div class="card-icon">🚨</div>
                    <h3>طباعة التنبيهات</h3>
                    <p>الأصناف الحرجة <span class="count-badge" id="print-alerts-count">0</span></p>
                </div>
                <div class="export-card" data-type="all" data-excel="true">
                    <div class="card-icon">📊</div>
                    <h3>Excel كامل</h3>
                    <p>تصدير Excel <span class="count-badge" id="excel-all-count">0</span></p>
                </div>
                <div class="export-card" data-type="alerts" data-excel="true">
                    <div class="card-icon">📋</div>
                    <h3>Excel تنبيهات</h3>
                    <p>التنبيهات فقط <span class="count-badge" id="excel-alerts-count">0</span></p>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    modal.querySelector('.modal-close').addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    modal.querySelectorAll('.export-card').forEach(card => {
        card.addEventListener('click', function() {
            const type = this.getAttribute('data-type');
            const isExcel = this.getAttribute('data-excel') === 'true';
            
            printSelection = type;
            
            modal.querySelectorAll('.export-card').forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            
            setTimeout(() => {
                if (isExcel) {
                    exportToExcel();
                } else {
                    openPrintPreview();
                }
                modal.style.display = 'none';
            }, 300);
        });
    });
    
    updateExportCounts();
}

// ✅ عرض المودال
function showExportModal() {
    const modal = document.getElementById('export-modal');
    if (modal) {
        modal.style.display = 'flex';
        updateExportCounts();
    }
}

// ✅ تحديث العدادات
function updateExportCounts() {
    const allTable = document.getElementById('allTable');
    if (!allTable) return;
    
    const allCount = allTable.querySelectorAll('tr:not(:first-child)').length;
    const alertsCount = allTable.querySelectorAll('tr.low, tr.zero').length;
    
    const updateBadge = (id, count) => {
        const badge = document.getElementById(id);
        if (badge) badge.textContent = count;
    };
    
    updateBadge('print-all-count', allCount);
    updateBadge('excel-all-count', allCount);
    updateBadge('print-alerts-count', alertsCount);
    updateBadge('excel-alerts-count', alertsCount);
}

// ✅ جلب بيانات الطباعة
function getPrintData() {
    const allTable = document.getElementById('allTable');
    if (!allTable) return '';
    
    const rows = allTable.querySelectorAll('tr:not(:first-child)');
    let html = '';
    let serial = 1;
    
    rows.forEach(row => {
        const shouldPrint = printSelection === 'all' || 
                           (printSelection === 'alerts' && 
                           (row.classList.contains('low') || row.classList.contains('zero')));
        
        if (shouldPrint && row.cells.length >= 5) {
            const cells = Array.from(row.cells).slice(0, 5);
            const rowClass = row.classList.contains('low') ? 'low' : 
                            row.classList.contains('zero') ? 'zero' : '';
            
            html += `
                <tr class="${rowClass}">
                    <td style="font-weight:bold;color:#4fc3f7;">${serial++}</td>
                    <td style="font-size:16px;font-weight:600;">${cells[0].textContent}</td>
                    <td style="font-family:monospace;font-weight:bold;">${cells[1].textContent}</td>
                    <td style="font-size:18px;color:#2e7d32;font-weight:bold;">${cells[2].textContent}</td>
                    <td>${cells[3].textContent}</td>
                    <td>${cells[4].textContent}</td>
                    <td style="color:#ff9800;font-weight:bold;">
                        ${row.classList.contains('zero') ? '🔴 نفد' : 
                          row.classList.contains('low') ? '🟠 قليل' : '✅ طبيعي'}
                    </td>
                </tr>
            `;
        }
    });
    
    return html || '<tr><td colspan="7" style="text-align:center;padding:50px;color:#999;font-size:18px;">لا توجد بيانات للعرض</td></tr>';
}

// ✅ جلب بيانات Excel
function getExcelData() {
    const allTable = document.getElementById('allTable');
    if (!allTable) return [];
    
    const rows = allTable.querySelectorAll('tr:not(:first-child)');
    const data = [];
    let serial = 1;
    
    rows.forEach(row => {
        const shouldExport = printSelection === 'all' || 
                            (printSelection === 'alerts' && 
                            (row.classList.contains('low') || row.classList.contains('zero')));
        
        if (shouldExport && row.cells.length >= 5) {
            const cells = Array.from(row.cells).slice(0, 5);
            data.push([
                serial++,
                cells[0].textContent,
                cells[2].textContent,
                cells[3].textContent,
                cells[4].textContent,
                row.classList.contains('zero') ? 'نفد المخزون' : 
                row.classList.contains('low') ? 'قليل المخزون' : 'طبيعي'
            ]);
        }
    });
    
    return data;
}

// ✅ فتح نافذة الطباعة
function openPrintPreview() {
    const printWindow = window.open('', '_blank', 'width=1200,height=800');
    if (!printWindow) {
        alert('❌ تم حظر نافذة الطباعة. تأكد من السماح بفتح النوافذ المنبثقة');
        return;
    }
    
    printWindow.document.write(getPrintHTML(getPrintData()));
    printWindow.document.close();
    
    setTimeout(() => printWindow.print(), 500);
}

// ✅ تصدير إلى Excel
function exportToExcel() {
    const data = getExcelData();
    if (data.length === 0) {
        alert('❌ لا توجد بيانات للتصدير');
        return;
    }
    
    const csv = convertToCSV(data);
    const filename = `مخازن_${printSelection}_${new Date().toISOString().split('T')[0]}.csv`;
    downloadCSV(csv, filename);
}

// ✅ إنشاء HTML للطباعة
function getPrintHTML(tableData) {
    const totalItems = document.querySelector('.card strong')?.textContent || '0';
    const title = printSelection === 'all' ? 'جميع الأصناف' : 'التنبيهات الحرجة';
    
    return `
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
            <meta charset="UTF-8">
            <title>📦 تقرير المخازن</title>
            <style>
                *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',Tahoma,sans-serif;direction:rtl}
                body{background:#f8f9ff;color:#333;padding:40px 30px;line-height:1.6;font-size:15px;max-width:1400px;margin:auto}
                .header{text-align:center;margin-bottom:50px;padding:40px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;border-radius:25px;box-shadow:0 20px 40px rgba(102,126,234,0.3)}
                .header h1{font-size:36px;margin-bottom:15px;text-shadow:0 4px 8px rgba(0,0,0,0.3)}
                .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:25px;margin:40px 0;text-align:center}
                .stat-card{background:white;padding:30px 20px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,0.1);border-left:6px solid #4fc3f7}
                .stat-card h3{font-size:32px;color:#4fc3f7;margin-bottom:10px}
                table{width:100%;border-collapse:collapse;margin:30px 0;box-shadow:0 20px 40px rgba(0,0,0,0.1);border-radius:20px;overflow:hidden}
                th{background:linear-gradient(45deg,#4fc3f7,#29b6f6);color:white;padding:20px 15px;font-weight:bold;text-align:center;font-size:16px}
                td{padding:18px 15px;text-align:center;border-bottom:1px solid #eee;font-size:15px}
                tr:nth-child(even){background:#f8f9ff}
                .low{background:#fff3e0!important;border-left:5px solid #ff9800}
                .zero{background:#ffebee!important;border-left:5px solid #f44336}
                @media print{body{padding:20px;font-size:13px;background:white}table{page-break-inside:avoid}}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📦 تقرير إدارة المخازن</h1>
                <p>${new Date().toLocaleDateString('ar-EG')} | ${new Date().toLocaleTimeString('ar-EG')}</p>
                <p style="font-size:22px;font-weight:bold;margin-top:15px;">${title}</p>
            </div>
            <div class="stats">
                <div class="stat-card">
                    <h3>${totalItems}</h3>
                    <p>إجمالي الأصناف</p>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>اسم الصنف</th>
                        <th>رقم الكرتون</th>
                        <th>الكمية الحالية</th>
                        <th>الحد الأدنى</th>
                        <th>المخزن</th>
                        <th>الحالة</th>
                    </tr>
                </thead>
                <tbody>${tableData}</tbody>
            </table>
            <p style="text-align:center;margin-top:40px;color:#999;font-size:12px;">
                تم الطباعة في: ${new Date().toLocaleString('ar-EG')}
            </p>
        </body>
        </html>
    `;
}

// ✅ تحويل إلى CSV
function convertToCSV(data) {
    const headers = ['المسلسل', 'الاسم', 'الكمية', 'الأرصدة', 'المخزن', 'الحالة'];
    const rows = data.map(row => 
        row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
    );
    return '\uFEFF' + [headers.join(','), ...rows].join('\n');
}

// ✅ تحميل ملف CSV
function downloadCSV(csv, filename) {
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}