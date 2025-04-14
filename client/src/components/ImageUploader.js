import React, { useRef } from 'react';
import './ImageUploader.css';

const IMAGE_SERVICE_URL = process.env.NODE_ENV === 'development' ? 'http://localhost:3003' : '';

const ImageUploader = ({ onUpload }) => {
  const fileInputRef = useRef(null);

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) {
      return;
    }

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    const token = localStorage.getItem('token');
    if (!token) {
      alert('Please login to upload images');
      return;
    }

    try {
      const response = await fetch(`${IMAGE_SERVICE_URL}/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();
      if (response.ok) {
        if (onUpload) {
          onUpload(data);
        }
      } else {
        alert(`Upload failed: ${data.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error during upload:', error);
      alert('Failed to upload image. Please try again.');
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) {
      return;
    }

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    // Call the parent's onUpload function with the event
    if (onUpload) {
      onUpload(e);
    }
  };

  return (
    <div className="image-uploader">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/*"
        style={{ display: 'none' }}
      />
      <button onClick={handleButtonClick} className="upload-button">
        Upload Image
      </button>
    </div>
  );
};

export default ImageUploader; 