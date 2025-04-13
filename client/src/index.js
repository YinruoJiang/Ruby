import React, { useState, useRef, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';

// Base URL for API requests
const API_BASE_URL = process.env.NODE_ENV === 'development' ? 'http://localhost:3001' : '';

function App() {
  const [uploadedImages, setUploadedImages] = useState([]);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchImages();
  }, []);

  async function fetchImages() {
    try {
      console.log('=== Fetching Images ===');
      const response = await fetch(`${API_BASE_URL}/api/images`);
      console.log('Response status:', response.status);
      
      if (response.ok) {
        const images = await response.json();
        console.log('Fetched images:', images);
        setUploadedImages(images);
      } else {
        console.error('Failed to fetch images:', response.status);
      }
    } catch (error) {
      console.error('Error fetching images:', error);
      console.error('Error details:', {
        message: error.message,
        stack: error.stack
      });
    }
  }

  const handleImageUpload = async (e) => {
    console.log('=== Image Upload Process Started ===');
    const file = e.target.files[0];
    if (!file) {
        console.log('No file selected');
        return;
    }
    console.log('Selected file:', {
      name: file.name,
      type: file.type,
      size: file.size
    });

    // Validate file type
    if (!file.type.startsWith('image/')) {
      console.error('Invalid file type:', file.type);
      alert('Please select an image file');
      return;
    }

    const formData = new FormData();
    formData.append('image', file);
    console.log('FormData created with file');

    try {
      console.log('Sending upload request...');
      const response = await fetch(`${API_BASE_URL}/api/upload-image`, {
          method: 'POST',
          body: formData,
      });
      console.log('Response status:', response.status);

      const data = await response.json();
      if (response.ok) {
        console.log('Upload successful, response:', data);
        fetchImages(); // Refresh the images list
        fileInputRef.current.value = ''; // Reset file input
      } else {
        console.error('Upload failed:', data);
        alert(`Upload failed: ${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error during upload:', error);
      console.error('Error details:', {
        message: error.message,
        stack: error.stack
      });
      alert('Failed to upload image. Please try again.');
    }
  };

  return (
    <div className="App">
      <h1>Ruby Board</h1>
      
      <div className="image-section">
        <div className="image-upload-container">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImageUpload}
            accept="image/*"
            style={{ display: 'none' }}
          />
          <button
            className="upload-button"
            onClick={() => fileInputRef.current.click()}
          >
            Upload Image
          </button>
        </div>

        <div className="image-gallery">
          <h3>Images for Ruby</h3>
          <div className="image-grid">
            {uploadedImages.length > 0 ? (
              uploadedImages.map((image) => (
                <div key={image.id} className="image-item">
                  <img 
                    src={`${API_BASE_URL}/${image.filename}`} 
                    alt={image.filename}
                    onError={(e) => {
                      console.error('Error loading image:', image.filename);
                      e.target.style.display = 'none';
                    }}
                  />
                </div>
              ))
            ) : (
              <p>No images uploaded yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

const container = document.getElementById('root');
const root = createRoot(container);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
); 