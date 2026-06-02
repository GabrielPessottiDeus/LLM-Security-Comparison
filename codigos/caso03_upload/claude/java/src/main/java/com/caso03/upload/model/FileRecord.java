package com.caso03.upload.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "file_records")
public class FileRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String filename;

    @Column(nullable = false)
    private Long size;

    @Column(nullable = false)
    private LocalDateTime uploadedAt;

    public FileRecord() {}

    public FileRecord(String filename, Long size, LocalDateTime uploadedAt) {
        this.filename = filename;
        this.size = size;
        this.uploadedAt = uploadedAt;
    }

    public Long getId() { return id; }
    public String getFilename() { return filename; }
    public Long getSize() { return size; }
    public LocalDateTime getUploadedAt() { return uploadedAt; }

    public void setId(Long id) { this.id = id; }
    public void setFilename(String filename) { this.filename = filename; }
    public void setSize(Long size) { this.size = size; }
    public void setUploadedAt(LocalDateTime uploadedAt) { this.uploadedAt = uploadedAt; }
}
