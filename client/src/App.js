import React, { useState, useEffect } from 'react';
import './App.css';
import ImageUploader from './components/ImageUploader';
import Login from './components/Login';

function App() {
  const [images, setImages] = useState([]);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (token) {
      verifyToken();
    }
  }, [token]);

  const verifyToken = async () => {
    try {
      const response = await fetch('http://localhost:3002/verify', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (response.ok) {
        setUsername(data.user);
        fetchImages();
      } else {
        handleLogout();
      }
    } catch (err) {
      handleLogout();
    }
  };

  const handleLogin = (newToken) => {
    setToken(newToken);
    localStorage.setItem('token', newToken);
  };

  const handleLogout = () => {
    setToken(null);
    setUsername('');
    localStorage.removeItem('token');
    setImages([]); // Clear images on logout
  };

  const fetchImages = async () => {
    try {
      const response = await fetch('http://localhost:3003/images', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        // Ensure data is an array before setting it
        setImages(Array.isArray(data.images) ? data.images : []);
      } else {
        setError('Failed to fetch images');
        setImages([]); // Set empty array on error
      }
    } catch (err) {
      setError('Failed to fetch images');
      setImages([]); // Set empty array on error
    }
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) {
      setError('No file selected');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:3003/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setError(''); // Clear any previous errors
        // Add the new image to the current images array
        setImages(prevImages => [...prevImages, {
          filename: data.filename,
          original_filename: data.original_filename,
          upload_date: new Date().toISOString()
        }]);
        e.target.value = ''; // Reset file input
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Failed to upload image');
      }
    } catch (err) {
      setError('Failed to upload image');
    }
  };

  const handleDeleteImage = async (filename) => {
    try {
      const response = await fetch(`http://localhost:3003/images/${filename}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        // Remove the image from the state
        setImages(prevImages => prevImages.filter(img => img.filename !== filename));
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Failed to delete image');
      }
    } catch (err) {
      setError('Failed to delete image');
    }
  };

  if (!token) {
    return (
      <div className="App">
        <Login onLogin={handleLogin} onRegister={handleLogin} />
      </div>
    );
  }

  return (
    <div className="App">
      <div className="content">
        <div className="user-info">
          <span>Welcome, {username}!</span>
          <button onClick={handleLogout} className="logout-button">Logout</button>
        </div>
        {error && <div className="error-message">{error}</div>}
        <ImageUploader onUpload={handleImageUpload} />
        <div className="image-grid">
          {images && images.length > 0 ? (
            images.map((image, index) => (
              <div key={index} className="image-item">
                <img src={`http://localhost:3003/uploads/${image.filename}`} alt={image.original_filename} />
                <div className="image-info">
                  <span className="image-name">{image.original_filename}</span>
                  <span className="image-date">{new Date(image.upload_date).toLocaleDateString()}</span>
                  <button 
                    className="delete-button"
                    onClick={() => handleDeleteImage(image.filename)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="no-images">No images uploaded yet</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App; 