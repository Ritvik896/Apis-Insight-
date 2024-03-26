// Function to update live data every second
function updateLiveData() {
    fetch('/get_data')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching live data:', data.error);
            } else {
                document.getElementById('temperature').innerText = `Temperature: ${data.temperature || 'N/A'} °C`;
                document.getElementById('humidity').innerText = `Humidity: ${data.humidity || 'N/A'}%`;
            }
        })
        .catch(error => console.error('Error fetching live data:', error))
        .finally(() => setTimeout(updateLiveData, 1000));  // Update every second
}

// Start updating live data on page load
document.addEventListener('DOMContentLoaded', updateLiveData);
