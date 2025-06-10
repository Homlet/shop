document.addEventListener('DOMContentLoaded', () => {
    // DOM elements
    const itemsContainer = document.getElementById('items-container');
    const resultSection = document.getElementById('result-section');
    const resultContainer = document.getElementById('result-container');
    const processBtn = document.getElementById('process-btn');
    const printBtn = document.getElementById('print-btn');
    const downloadBtn = document.getElementById('download-btn');
    const backBtn = document.getElementById('back-btn');
    const storeSelect = document.getElementById('store-select');
    const loadingOverlay = document.getElementById('loading-overlay');
    const moreItemsSection = document.getElementById('more-items');
    const remainingCount = document.getElementById('remaining-count');
    
    // State
    let processedContent = null;
    const defaultItemLimit = 5;
    
    // Fetch and display shopping list items
    async function fetchItems() {
        const limit = defaultItemLimit;
        try {
            itemsContainer.innerHTML = '<p class="loading">Loading items...</p>';
            moreItemsSection.style.display = 'none';
            
            const response = await fetch(`api/items${limit ? `?limit=${limit}` : ''}`);
            const data = await response.json();
            
            if (data.items && data.items.length > 0) {
                renderItems(data.items);
                
                // Show "and X more items" if truncated
                if (data.truncated) {
                    const remaining = data.total_count - data.items.length;
                    remainingCount.textContent = remaining;
                    moreItemsSection.style.display = 'block';
                }
            } else {
                itemsContainer.innerHTML = '<p>Your shopping list is empty. Try adding some items in Home Assistant.</p>';
            }
        } catch (error) {
            console.error('Error fetching items:', error);
            itemsContainer.innerHTML = '<p class="error">Failed to load items. Please check your connection and try again.</p>';
        }
    }
    
    // Render list items in the UI
    function renderItems(items) {
        itemsContainer.innerHTML = '';
        
        const list = document.createElement('ul');
        list.className = 'items-list';
        
        items.forEach(item => {
            const listItem = document.createElement('li');
            listItem.className = 'item-entry';
            
            // Create item name span
            const itemName = document.createElement('span');
            itemName.textContent = item.name;
            itemName.className = 'item-name';
            listItem.appendChild(itemName);
            
            list.appendChild(listItem);
        });
        
        itemsContainer.appendChild(list);
    }
    
    // Process the shopping list through the LLM
    async function processShoppingList() {
        // Show loading overlay
        loadingOverlay.style.display = 'flex';
        
        try {
            const storeName = storeSelect.value;
            const response = await fetch(`api/process?store_name=${encodeURIComponent(storeName)}&format_type=text`);
            const data = await response.json();
            
            // Store the processed content
            processedContent = data.content;
            
            // Display the result
            resultContainer.textContent = processedContent;
            resultSection.style.display = 'block';
            
            // Scroll to result section
            resultSection.scrollIntoView({ behavior: 'smooth' });
            
        } catch (error) {
            console.error('Error processing list:', error);
            alert('Failed to process the list. Please try again.');
        } finally {
            // Hide loading overlay
            loadingOverlay.style.display = 'none';
        }
    }
    
    // Print the processed list
    function printList() {
        if (!processedContent) return;
        
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Shopping List</title>
                <style>
                    body {
                        font-family: monospace;
                        width: 58mm;
                        margin: 0;
                        padding: 10px;
                    }
                    pre {
                        white-space: pre-wrap;
                        margin: 0;
                    }
                </style>
            </head>
            <body>
                <pre>${processedContent}</pre>
                <script>
                    window.onload = function() {
                        window.print();
                        setTimeout(function() { window.close(); }, 500);
                    };
                </script>
            </body>
            </html>
        `);
        printWindow.document.close();
    }
    
    // Download the processed list as a text file
    function downloadList() {
        if (!processedContent) return;
        
        const blob = new Blob([processedContent], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'shopping-list.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    // Go back to the items view
    function goBack() {
        resultSection.style.display = 'none';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    // Fetch stores for the dropdown
    async function fetchStores() {
        try {
            const response = await fetch('api/stores');
            const data = await response.json();
            
            if (data.stores && data.stores.length > 0) {
                storeSelect.innerHTML = '';
                
                data.stores.forEach(store => {
                    const option = document.createElement('option');
                    option.value = store.name;
                    option.textContent = store.name;
                    storeSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error fetching stores:', error);
        }
    }
    
    // Event listeners
    processBtn.addEventListener('click', processShoppingList);
    printBtn.addEventListener('click', printList);
    downloadBtn.addEventListener('click', downloadList);
    backBtn.addEventListener('click', goBack);
    
    // Initialize
    fetchItems();
    fetchStores();
});