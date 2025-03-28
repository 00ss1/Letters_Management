import React, { useState, useEffect } from "react";
import axios from "axios";
// import "./LetterEditor.css";
import { Editor } from "@tinymce/tinymce-react";

function LetterEditor({ onLogout }) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [letters, setLetters] = useState([]);
  const [selectedLetterId, setSelectedLetterId] = useState(null);
  const [email, setEmail] = useState("aryaa3957@gmail.com");

  useEffect(() => {
    fetchLetters();
  }, []);

  const fetchLetters = async () => {
    try {
      const response = await axios.get(
        `http://127.0.0.1:5000/get-letters/${email}`,
        { withCredentials: true } // Added withCredentials
      );
      setLetters(response.data);
    } catch (error) {
      console.error("Error fetching letters:", error);
    }
  };

  const handleSave = async () => {
    if (!title.trim()) {
      alert("Title cannot be empty!");
      return;
    }
    if (!content.trim()) {
      alert("Letter content cannot be empty!");
      return;
    }

    try {
      if (selectedLetterId) {
        await axios.put(
          `http://127.0.0.1:5000/update-letter/${selectedLetterId}`,
          {
            title,
            content,
          },
          { withCredentials: true } // Ensure authentication cookies are sent
        );
        alert("Letter updated!");
      } else {
        await axios.post(
          "http://127.0.0.1:5000/save-letter",
          {
            email,
            title,
            content,
          },
          { withCredentials: true }
        );
        alert("Letter saved!");
      }
      fetchLetters(); // Refresh saved letters list
      setTitle("");
      setContent("");
      setSelectedLetterId(null);
    } catch (error) {
      console.error("Error saving/updating letter:", error);
    }
  };

  const handleSelectLetter = async (letterId) => {
    try {
      const response = await axios.get(
        `http://127.0.0.1:5000/get-letter/${letterId}`,
        { withCredentials: true } // Added withCredentials
      );
      setTitle(response.data.title);
      setContent(response.data.content);
      setSelectedLetterId(letterId);
    } catch (error) {
      console.error("Error fetching letter:", error);
    }
  };

  const handleDelete = async (letterId) => {
    try {
      console.log("Deleting letter with ID:", letterId);
      await axios.delete(`http://127.0.0.1:5000/delete-letter/${letterId}`, {
        withCredentials: true, // Added withCredentials
      });
      console.log("Letter deleted:", letterId);
      alert("Letter deleted!");
      fetchLetters();
      setTitle("");
      setContent("");
      setSelectedLetterId(null);
    } catch (error) {
      console.error("Error deleting letter:", error);
    }
  };

  function saveLetterToDrive(email, title, content) {
    fetch("http://127.0.0.1:5000/save-to-drive", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, title, content }),
      credentials: "include", // Added credentials
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.document_link) {
          displayDocumentLink(data.document_link);
        } else {
          console.error("Error saving to Google Drive:", data.message);
          displayErrorMessage("Failed to save to Google Drive.");
        }
      })
      .catch((error) => {
        console.error("Network error:", error);
        displayErrorMessage("Network error. Please try again.");
      });
  }

  function displayDocumentLink(link) {
    const linkElement = document.createElement("a");
    linkElement.href = link;
    linkElement.textContent = "Open Google Doc";
    const linkContainer = document.getElementById("documentLinkContainer");
    linkContainer.innerHTML = "";
    linkContainer.appendChild(linkElement);
  }

  function displayErrorMessage(message) {
    alert(message);
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "20px",
      }}
    >
      <h2 style={{ textAlign: "center", color: "green" }}>LetterEditor</h2>

      {/* Title Input with Red Label */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <label
          style={{
            color: "red",
            fontSize: "18px",
            fontWeight: "bold",
            textAlign: "center",
          }}
        >
          Title
        </label>
        <input
          type="text"
          placeholder="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          style={{
            width: "300px",
            padding: "8px",
            fontSize: "16px",
            border: "1px solid #ccc",
            borderRadius: "5px",
            textAlign: "center",
          }}
        />
      </div>

      <Editor
        apiKey="av12zmk3jsvn1paevc879gaxwb3ph4l6qlipbkxxwdn1kigw" // Replace with your TinyMCE API key
        value={content}
        onEditorChange={(newContent, editor) => {
          setContent(newContent);
        }}
        init={{
          menubar: true, // Show the menu bar
          plugins: [
            "advlist autolink lists link image charmap print preview anchor",
            "searchreplace visualblocks code fullscreen",
            "insertdatetime media table paste code help wordcount",
          ],
          toolbar:
            "undo redo | formatselect | " +
            "bold italic backcolor | alignleft aligncenter " +
            "alignright alignjustify | bullist numlist outdent indent | " +
            "removeformat | help",
        }}
        style={{
          width: "800px",
          height: "300px",
          marginBottom: "20px",
          color: "black",
          border: "4px solid black",
          borderRadius: "5px",
          padding: "10px",
        }}
      />

      <div id="documentLinkContainer"></div>

      {/* Button Container */}
      <div style={{ display: "flex", gap: "20px", marginTop: "20px" }}>
        <button
          style={{
            backgroundColor: "blue",
            color: "white",
            padding: "10px 15px",
            border: "none",
            borderRadius: "8px",
            fontSize: "20px",
          }}
          onClick={handleSave}
        >
          {selectedLetterId ? "Update Letter" : "Save Letter"}
        </button>

        <button
          style={{
            backgroundColor: "blue",
            color: "white",
            padding: "10px 15px",
            border: "none",
            borderRadius: "8px",
            fontSize: "20px",
          }}
          onClick={() => saveLetterToDrive(email, title, content)}
        >
          Save to Google Drive
        </button>

        <button
          style={{
            backgroundColor: "black",
            color: "red",
            padding: "10px 15px",
            border: "none",
            borderRadius: "8px",
            fontSize: "20px",
          }}
          onClick={onLogout}
        >
          Logout
        </button>
      </div>

      <h2>Saved Letters</h2>
      <ul>
        {letters.map((letter) => (
          <li key={letter._id} style={{ marginBottom: "10px" }}>
            {letter.title}
            <div style={{ display: "flex", gap: "10px", marginTop: "5px" }}>
              <button
                style={{
                  backgroundColor: "black",
                  color: "green",
                  padding: "10px 15px",
                  border: "none",
                  borderRadius: "8px",
                  fontSize: "20px",
                }}
                onClick={() => handleSelectLetter(letter._id)}
              >
                Edit
              </button>
              <button
                style={{
                  backgroundColor: "blue",
                  color: "red",
                  padding: "10px 15px",
                  border: "none",
                  borderRadius: "8px",
                  fontSize: "20px",
                }}
                onClick={() => handleDelete(letter._id)}
              >
                Delete
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default LetterEditor;
