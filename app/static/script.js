document.addEventListener('DOMContentLoaded', () => {
    // DOM elements
    const listsContainer = document.getElementById('lists-container');
    const itemsContainer = document.getElementById('items-container');
    const itemsSection = document.getElementById('items-section');
    const resultSection = document.getElementById('result-section');
    const resultContainer = document.getElementById('result-container');
    const processBtn = document.getElementById('process-btn');
    const printBtn = document.getElementById('print-btn');
    const downloadBtn = document.getElementById('download-btn');
    const backBtn = document.getElementById('back-btn');
    const storeSelect = document.getElementById('store-select');
    const loadingOverlay = document.getElementById('loading-overlay');
    
    // State
    let selectedListId = null;
    let processedContent = null;
    
    // Fetch and display available lists
    async function fetchLists() {
        try {
            const response = await fetch('/api/lists');
            const data = await response.json();
            
            if (data.lists && data.lists.length > 0) {
                renderLists(data.lists);
            } else {
                listsContainer.innerHTML = '<p>No lists available. Try adding items to your AnyList.</p>';
            }
        } catch (error) {
            console.error('Error fetching lists:', error);
            listsContainer.innerHTML = '<p class="error">Failed to load lists. Please check your connection and try again.</p>';
        }
    }
    
    // Render lists in the UI
    function renderLists(lists) {
        listsContainer.innerHTML = '';
        
        lists.forEach(list => {
            const listEl = document.createElement('div');
            listEl.className = 'list-item';
            listEl.textContent = list.name;
            listEl.dataset.id = list.id;
            
            listEl.addEventListener('click', () => {
                document.querySelectorAll('.list-item').forEach(el => el.classList.remove('selected'));
                listEl.classList.add('selected');
                selectedListId = list.id;
                fetchListItems(list.id);
            });
            
            listsContainer.appendChild(listEl);
        });
    }
    
    // Fetch items from a selected list
    async function fetchListItems(listId) {
        itemsContainer.innerHTML = '<p class="loading">Loading items...</p>';
        itemsSection.style.display = 'block';
        
        try {
            const response = await fetch(`/api/lists/${listId}/items`);
            const data = await response.json();
            
            if (data.items && data.items.length > 0) {
                renderItems(data.items);
            } else {
                itemsContainer.innerHTML = '<p>This list is empty. Add some items first.</p>';
            }
        } catch (error) {
            console.error('Error fetching list items:', error);
            itemsContainer.innerHTML = '<p class="error">Failed to load items. Please try again.</p>';
        }
    }
    
    // Render list items in the UI
    function renderItems(items) {
        itemsContainer.innerHTML = '';
        
        const list = document.createElement('ul');
        list.className = 'items-list';
        
        items.forEach(item => {
            const listItem = document.createElement('li');
            listItem.textContent = item.name;
            list.appendChild(listItem);
        });
        
        itemsContainer.appendChild(list);
    }
    
    // Process a list through the LLM
    async function processShoppingList() {
        if (!selectedListId) {
            alert('Please select a list first');
            return;
        }
        
        // Show loading overlay
        loadingOverlay.style.display = 'flex';
        
        try {
            const storeName = storeSelect.value;
            const response = await fetch(`/api/lists/${selectedListId}/process?store_name=${encodeURIComponent(storeName)}&format_type=text`);
            const data = await response.json();
            
            // Store the processed content
            processedContent = data.content;
            
            // Display the result
            resultContainer.textContent = processedContent;
            resultSection.style.display = 'block';
            
            // Hide other sections
            itemsSection.style.display = 'none';
            
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
        itemsSection.style.display = 'block';
    }
    
    // Event listeners
    processBtn.addEventListener('click', processShoppingList);
    printBtn.addEventListener('click', printList);
    downloadBtn.addEventListener('click', downloadList);
    backBtn.addEventListener('click', goBack);
    
    // Fetch stores for the dropdown
    async function fetchStores() {
        try {
            const response = await fetch('/api/stores');
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
    
    // Initialize
    fetchLists();
    fetchStores();
});