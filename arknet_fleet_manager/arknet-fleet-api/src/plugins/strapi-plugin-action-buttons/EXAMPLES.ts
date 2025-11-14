/**
 * Example Button Handlers
 * 
 * This file contains example implementations of button handlers for the
 * strapi-plugin-action-buttons plugin. Copy these examples to your
 * src/admin/button-handlers.ts file and customize as needed.
 */

// TypeScript declarations for window object
declare global {
  interface Window {
    handleSendEmail: (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => void;
    handleUploadCSV: (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => void;
    handleGenerateReport: (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => void;
    handleSyncToCRM: (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => void;
    handleDefaultAction: (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => void;
  }
}

/**
 * Example 1: Send Email Notification
 * Usage in schema: "onClick": "handleSendEmail"
 */
window.handleSendEmail = async (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => {
  console.log('Send Email clicked!', fieldName, fieldValue);
  
  const confirmed = confirm('Send email notification?');
  if (!confirmed) return;
  
  alert('Sending email...');
  
  try {
    // Example: Get auth token and entry ID
    const token = localStorage.getItem('jwtToken');
    const entryId = window.location.pathname.split('/').pop();
    
    // Example API call
    const response = await fetch('/api/notifications/send', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ entryId })
    });
    
    const result = await response.json();
    
    // Store metadata
    if (onChange) {
      onChange({
        emailSent: true,
        sentAt: new Date().toISOString(),
        recipientCount: result.recipientCount || 1,
        status: 'success'
      });
    }
    
    alert('✅ Email sent successfully!');
  } catch (error) {
    console.error('Error sending email:', error);
    alert('❌ Failed to send email');
    
    if (onChange) {
      onChange({
        emailSent: false,
        error: (error as Error).message,
        attemptedAt: new Date().toISOString(),
        status: 'failed'
      });
    }
  }
};

/**
 * Example 2: Upload CSV File
 * Usage in schema: "onClick": "handleUploadCSV"
 */
window.handleUploadCSV = async (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => {
  console.log('Upload CSV clicked!', fieldName, fieldValue);
  
  // Create file input
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.csv';
  
  input.onchange = async (e: any) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = async (event) => {
      const csvContent = event.target?.result as string;
      const rows = csvContent.split('\n');
      
      console.log('CSV rows:', rows.length);
      
      // Store metadata
      if (onChange) {
        onChange({
          uploaded: true,
          fileName: file.name,
          fileSize: file.size,
          rowCount: rows.length - 1, // Subtract header row
          uploadedAt: new Date().toISOString(),
          status: 'success'
        });
      }
      
      alert(`✅ Uploaded ${file.name}\nRows: ${rows.length - 1}`);
    };
    
    reader.readAsText(file);
  };
  
  input.click();
};

/**
 * Example 3: Generate Report
 * Usage in schema: "onClick": "handleGenerateReport"
 */
window.handleGenerateReport = async (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => {
  console.log('Generate Report clicked!', fieldName, fieldValue);
  
  alert('Generating report...');
  
  try {
    const entryId = window.location.pathname.split('/').pop();
    const token = localStorage.getItem('jwtToken');
    
    // Simulate report generation
    const response = await fetch(`/api/reports/generate/${entryId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    const result = await response.json();
    
    if (onChange) {
      onChange({
        reportGenerated: true,
        reportId: result.reportId,
        reportUrl: result.url,
        generatedAt: new Date().toISOString(),
        status: 'success'
      });
    }
    
    alert(`✅ Report generated!\nID: ${result.reportId}`);
    
    // Optionally open report in new tab
    if (result.url) {
      window.open(result.url, '_blank');
    }
  } catch (error) {
    console.error('Error generating report:', error);
    alert('❌ Failed to generate report');
    
    if (onChange) {
      onChange({
        reportGenerated: false,
        error: (error as Error).message,
        attemptedAt: new Date().toISOString(),
        status: 'failed'
      });
    }
  }
};

/**
 * Example 4: Sync to External CRM
 * Usage in schema: "onClick": "handleSyncToCRM"
 */
window.handleSyncToCRM = async (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => {
  console.log('Sync to CRM clicked!', fieldName, fieldValue);
  
  const confirmed = confirm('Sync this entry to CRM?');
  if (!confirmed) return;
  
  try {
    const entryId = window.location.pathname.split('/').pop();
    const token = localStorage.getItem('jwtToken');
    
    // Get entry data
    const contentType = window.location.pathname.split('/')[3]; // e.g., 'article'
    const entry = await fetch(`/api/${contentType}s/${entryId}?populate=*`, {
      headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());
    
    // Sync to CRM
    const syncResult = await fetch('https://crm-api.example.com/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'your-api-key'
      },
      body: JSON.stringify(entry)
    }).then(r => r.json());
    
    if (onChange) {
      onChange({
        synced: true,
        syncedAt: new Date().toISOString(),
        crmId: syncResult.id,
        crmUrl: syncResult.url,
        status: 'success'
      });
    }
    
    alert(`✅ Synced to CRM!\nCRM ID: ${syncResult.id}`);
  } catch (error) {
    console.error('Error syncing to CRM:', error);
    alert('❌ Sync failed');
    
    if (onChange) {
      onChange({
        synced: false,
        error: (error as Error).message,
        attemptedAt: new Date().toISOString(),
        status: 'failed'
      });
    }
  }
};

/**
 * Example 5: Default Action (Simple Example)
 * Usage in schema: "onClick": "handleDefaultAction"
 */
window.handleDefaultAction = async (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => {
  console.log('Default action clicked!', fieldName, fieldValue);
  
  alert('Button clicked! This is the default handler.');
  
  // Track click history
  const previousClicks = fieldValue?.clicks || [];
  const newClick = {
    timestamp: new Date().toISOString(),
    user: localStorage.getItem('username') || 'unknown'
  };
  
  if (onChange) {
    onChange({
      clicks: [...previousClicks, newClick],
      lastClick: newClick.timestamp,
      totalClicks: previousClicks.length + 1
    });
  }
  
  alert(`Total clicks: ${previousClicks.length + 1}`);
};

// Export to satisfy TypeScript module system
export {};
