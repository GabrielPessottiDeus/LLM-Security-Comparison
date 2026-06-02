package com.caso03.upload.repository;

import com.caso03.upload.model.FileRecord;
import org.springframework.data.jpa.repository.JpaRepository;

public interface FileRepository extends JpaRepository<FileRecord, Long> {
}
