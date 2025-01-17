document.addEventListener('DOMContentLoaded', () => {
    // Fetch HS Code based on product name
    const fetchHsCodeButton = document.getElementById('fetch-hs-code');
    if (fetchHsCodeButton) {
        fetchHsCodeButton.addEventListener('click', () => {
            // Show temporary info message
            alert('After clicking the Fetch HS Code button, TradesphereChat AI will automatically suggest the most suitable HS Code. If the correct code is not retrieved, click the button again. You can also select the exact product from the below Commodity Details, which will display after some part of the given entry. Once the additional details are no longer needed, please remove them from the entry below (HS CODE).');

            const productName = document.getElementById('final-product').value.trim();
            if (!productName) {
                alert('Please enter a product name.');
                return;
            }

            fetch('/fetch-hs-code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ product_name: productName }),
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.error) {
                        alert(data.error);
                    } else {
                        const hsCodeInput = document.getElementById('hs-code');
                        if (hsCodeInput) {
                            hsCodeInput.value = data.hs_code;
                            finalProduct = productName;
                        }
                    }
                })
                .catch((error) => console.error('Error fetching HS Code:', error));
        });
    }


    // Fetch HS Code info
    const fetchInfoButton = document.getElementById('fetch-info');
    if (fetchInfoButton) {
        fetchInfoButton.addEventListener('click', () => {
            alert('Fetching information, please wait... This may take some time.');
            const hsCode = document.getElementById('hs-code').value.trim();
            if (!hsCode) {
                alert('Please enter an HS Code.');
                return;
            }

            fetch(`/hs-code-info/${hsCode}`)
                .then((response) => response.json())
                .then((data) => {
                    if (data.error) {
                        alert(data.error);
                    } else {
                        const tableBody = document.getElementById('commodity-table').querySelector('tbody');
                        if (tableBody) {
                            tableBody.innerHTML = ''; // Clear existing rows

                            data.matched_commodities.forEach((row) => {
                                const newRow = tableBody.insertRow();
                                newRow.innerHTML = `
                                    <td><input type="checkbox" data-hs="${row.hs_code}"></td>
                                    <td>${row.hs_code}</td>
                                    <td>${row.description}</td>
                                    <td>${row.rule_of_origin}</td>
                                `;
                            });
                        }
                    }
                })
                .catch((error) => console.error('Error fetching HS Code info:', error));
        });
    }

    // Save selected HS Code data
    const saveSelectedButton = document.getElementById('save-selected');
    if (saveSelectedButton) {
        saveSelectedButton.addEventListener('click', () => {
            alert('Saving Details, please wait...');
            const selectedData = Array.from(
                document.querySelectorAll('#commodity-table input:checked')
            ).map((input) => {
                const row = input.closest('tr');
                return {
                    hs_code: row.cells[1].textContent.trim(),
                    description: row.cells[2].textContent.trim(),
                    rule_of_origin: row.cells[3].textContent.trim(),
                };
            });

            if (selectedData.length > 0) {
                const payload = {
                    final_product: finalProduct,
                    selected_data: selectedData,
                };

                fetch('/save-selected-data', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload),
                })
                    .then((response) => response.json())
                    .then((data) => {
                        if (data.success) {
                            alert('Selected data saved successfully!');
                            const downloadButton = document.getElementById('download-report');
                            if (downloadButton) {
                                downloadButton.href = `/pdf_report/${data.report_name}`; // Dynamically set the report name
                                downloadButton.style.display = 'block';
                                downloadButton.disabled = false;
                            }
                        } else {
                            alert('Failed to save data: ' + data.error);
                        }
                    })
                    .catch((error) => console.error('Error saving data:', error));
            } else {
                alert('No data selected.');
            }
        });
    }

    // Handle file upload
    const uploadForm = document.getElementById('upload-form');
if (uploadForm) {
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        alert('The processed file will be available for download shortly');
        const formData = new FormData(e.target);

        try {
            // Send the file to the server
            const response = await fetch('/process-file', { method: 'POST', body: formData });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Error: ${response.statusText}`);
            }

            const result = await response.json(); // Parse the server response as JSON

            if (result.download_url) {
                // Create a hidden anchor tag to trigger download
                const downloadLink = document.createElement('a');
                downloadLink.href = result.download_url; // Set the download URL
                downloadLink.download = 'Enhanced_Summary_Report.pdf'; // Suggested file name
                document.body.appendChild(downloadLink);
                downloadLink.click(); // Trigger the download
                document.body.removeChild(downloadLink); // Clean up
                alert('File downloaded successfully!');
            } else if (result.message) {
                alert(result.message); // Inform the user about the processing status
            } else {
                throw new Error('Unexpected server response.');
            }
        } catch (error) {
            console.error('File upload error:', error);
            alert('Failed to process the file. Please check your connection and try again.');
        }
    });
}

});
