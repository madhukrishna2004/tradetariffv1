document.addEventListener('DOMContentLoaded', () => {
    // Create spinner element
    const spinner = document.createElement('div');
    spinner.classList.add('spinner');
    document.body.appendChild(spinner);

    // Add spinner squares
    for (let i = 0; i < 4; i++) {
        const square = document.createElement('div');
        spinner.appendChild(square);
    }

    spinner.style.display = 'none'; // Initially hidden
    
    let finalProduct = ""; 

    // Fetch HS Code based on product name
    const fetchHsCodeButton = document.getElementById('fetch-hs-code');
    if (fetchHsCodeButton) {
        fetchHsCodeButton.addEventListener('click', () => {
            spinner.style.display = 'block';
            const content = document.getElementById('content');
            if (content) {
                content.style.display = 'none';
            }

            const productName = document.getElementById('final-product').value.trim();
            if (!productName) {
                alert('Please enter a product name.');
                spinner.style.display = 'none';
                if (content) {
                    content.style.display = 'block';
                }
                return;
            }

            // Set finalProduct to productName, so it's available later for saving
            finalProduct = productName;

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
                        }
                    }
                })
                .catch((error) => console.error('Error fetching HS Code:', error))
                .finally(() => {
                    spinner.style.display = 'none';
                    if (content) {
                        content.style.display = 'block';
                    }
                });
        });
    }

    // Fetch HS Code info
    const fetchInfoButton = document.getElementById('fetch-info');
    if (fetchInfoButton) {
        fetchInfoButton.addEventListener('click', () => {
            spinner.style.display = 'block';
            const content = document.getElementById('content');
            if (content) {
                content.style.display = 'none';
            }

            alert('Fetching information, please wait... This may take some time.');

            const hsCode = document.getElementById('hs-code').value.trim();
            if (!hsCode) {
                alert('Please enter an HS Code.');
                spinner.style.display = 'none';
                if (content) {
                    content.style.display = 'block';
                }
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
                .catch((error) => console.error('Error fetching HS Code info:', error))
                .finally(() => {
                    spinner.style.display = 'none';
                    if (content) {
                        content.style.display = 'block';
                    }
                });
        });
    }

    // Save selected HS Code data
    const saveSelectedButton = document.getElementById('save-selected');
    if (saveSelectedButton) {
        saveSelectedButton.addEventListener('click', () => {
            spinner.style.display = 'block';
            const content = document.getElementById('content');
            if (content) {
                content.style.display = 'none';
            }

            const hsCodeInput = document.getElementById('hs-code');
            if (!hsCodeInput || !hsCodeInput.value.trim()) {
                alert('Please enter a valid HS Code.');
                spinner.style.display = 'none';
                if (content) content.style.display = 'block';
                return;
            }

            // If finalProduct is not set yet, get it from the input field
            if (!finalProduct) {
                finalProduct = document.getElementById('final-product').value.trim();
            }

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

            if (selectedData.length === 0) {
                alert('No commodities selected. Please select at least one row.');
                spinner.style.display = 'none';
                if (content) content.style.display = 'block';
                return;
            }

            const payload = {
                final_product: finalProduct,
                selected_data: selectedData,
            };

            console.log("Payload being sent: ", payload);

            let loadingTimeout = setTimeout(() => {
                alert('Request is taking longer than expected. Please try again later.');
                spinner.style.display = 'none';
                if (content) content.style.display = 'block';
            }, 10000); // 10 seconds

            fetch('/save-selected-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            })
                .then((response) => response.json())
                .then((data) => {
                    clearTimeout(loadingTimeout); // Clear timeout if successful
                    if (data.success) {
                        alert('Selected data saved successfully!');
                        const downloadButton = document.getElementById('download-report');
                        if (downloadButton) {
                            downloadButton.href = `/pdf_report/${data.report_name}`;
                            downloadButton.style.display = 'block';
                            downloadButton.disabled = false;
                        }
                    } else {
                        alert('Failed to save data: ' + data.error);
                    }
                })
                .catch((error) => {
                    clearTimeout(loadingTimeout);
                    console.error('Error saving data:', error);
                    alert('Failed to save data. Please try again.');
                })
                .finally(() => {
                    spinner.style.display = 'none';
                    if (content) content.style.display = 'block';
                });
        });
    }

    // Handle file upload
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            spinner.style.display = 'block';
            const content = document.getElementById('content');
            if (content) {
                content.style.display = 'none';
            }

            alert('The processed file will be available for download shortly');
            const formData = new FormData(e.target);

            try {
                const response = await fetch('/process-file', { method: 'POST', body: formData });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `Error: ${response.statusText}`);
                }

                const result = await response.json();

                if (result.download_url) {
                    const downloadLink = document.createElement('a');
                    downloadLink.href = result.download_url;
                    downloadLink.download = 'Enhanced_Summary_Report.pdf';
                    document.body.appendChild(downloadLink);
                    downloadLink.click();
                    document.body.removeChild(downloadLink);
                    alert('File downloaded successfully!');
                } else if (result.message) {
                    alert(result.message);
                } else {
                    throw new Error('Unexpected server response.');
                }
            } catch (error) {
                console.error('File upload error:', error);
                alert('Failed to process the file. Please check your connection and try again.');
            } finally {
                spinner.style.display = 'none';
                if (content) {
                    content.style.display = 'block';
                }
            }
        });
    }
});
