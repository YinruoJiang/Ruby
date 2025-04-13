import React, { useRef } from 'react';
import './ImageUploader.css';

const API_BASE_URL = process.env.NODE_ENV === 'development' ? 'http://localhost:3001' : '';

function ImageUploader({ onImageUploaded }) {
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
    formData.append('image', file);

    try {
      const response = await fetch(`${API_BASE_URL}/api/upload-image`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (response.ok) {
        fileInputRef.current.value = ''; // Reset file input
        if (onImageUploaded) {
          onImageUploaded(data);
        }
      } else {
        alert(`Upload failed: ${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error during upload:', error);
      alert('Failed to upload image. Please try again.');
    }
  };

  return (
    <div className="image-uploader">
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
  );
}

export default ImageUploader; 