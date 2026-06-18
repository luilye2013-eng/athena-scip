/**
 * Athena SCIP - Utility Functions
 * Reusable, maintainable, and SOLID-compliant utilities
 */

// Check if already defined to prevent duplicate declaration
if (typeof window.DataExporter === 'undefined') {

class DataExporter {
    /**
     * Export data to CSV format
     */
    static toCSV(data, filename = 'export', headers = null) {
        if (!data || data.length === 0) {
            console.warn('No data to export');
            return;
        }
        
        const headerRow = headers || Object.keys(data[0]);
        const csvRows = [];
        csvRows.push(headerRow.join(','));
        
        for (const row of data) {
            const values = headerRow.map(header => {
                const value = row[header] ?? '';
                return typeof value === 'string' && value.includes(',') 
                    ? `"${value}"` 
                    : value;
            });
            csvRows.push(values.join(','));
        }
        
        const csvContent = csvRows.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        URL.revokeObjectURL(link.href);
    }
    
    static toJSON(data, filename = 'export') {
        const jsonContent = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `${filename}_${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        URL.revokeObjectURL(link.href);
    }
}

class DateUtils {
    static getDateRange(days) {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - days);
        return { startDate, endDate };
    }
    
    static formatDate(date, format = 'short') {
        const d = new Date(date);
        if (format === 'short') return d.toLocaleDateString();
        if (format === 'long') return d.toLocaleString();
        return d.toISOString().split('T')[0];
    }
}

class ValidationUtils {
    static isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
    
    static isStrongPassword(password) {
        return password && password.length >= 8;
    }
}

// Expose globally
window.DataExporter = DataExporter;
window.DateUtils = DateUtils;
window.ValidationUtils = ValidationUtils;

} // End of if undefined check

// Ensure exports are available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DataExporter, DateUtils, ValidationUtils };
}