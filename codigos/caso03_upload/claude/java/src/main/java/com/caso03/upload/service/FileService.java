package com.caso03.upload.service;

import com.caso03.upload.model.FileRecord;
import com.caso03.upload.repository.FileRepository;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.net.MalformedURLException;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class FileService {

    @Value("${file.upload-dir}")
    private String uploadDir;

    private Path uploadPath;

    private final FileRepository fileRepository;

    public FileService(FileRepository fileRepository) {
        this.fileRepository = fileRepository;
    }

    @PostConstruct
    public void init() throws IOException {
        uploadPath = Paths.get(uploadDir).toAbsolutePath().normalize();
        Files.createDirectories(uploadPath);
    }

    public String store(MultipartFile file) throws IOException {
        String filename = Paths.get(file.getOriginalFilename()).getFileName().toString();
        Path target = uploadPath.resolve(filename);
        Files.copy(file.getInputStream(), target, StandardCopyOption.REPLACE_EXISTING);

        FileRecord record = new FileRecord(filename, file.getSize(), LocalDateTime.now());
        fileRepository.save(record);

        return filename;
    }

    public Resource load(String filename) throws MalformedURLException {
        Path file = uploadPath.resolve(filename).normalize();
        Resource resource = new UrlResource(file.toUri());
        if (!resource.exists() || !resource.isReadable()) {
            throw new RuntimeException("File not found: " + filename);
        }
        return resource;
    }

    public List<String> listFiles() throws IOException {
        try (var stream = Files.list(uploadPath)) {
            return stream
                    .filter(Files::isRegularFile)
                    .map(p -> p.getFileName().toString())
                    .sorted()
                    .collect(Collectors.toList());
        }
    }
}
