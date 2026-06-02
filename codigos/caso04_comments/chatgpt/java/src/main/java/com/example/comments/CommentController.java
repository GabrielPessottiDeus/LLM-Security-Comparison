package com.example.comments;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.List;

@Controller
public class CommentController {

    private final CommentRepository commentRepository;

    public CommentController(CommentRepository commentRepository) {
        this.commentRepository = commentRepository;
    }

    @GetMapping("/")
    public String index(Model model) {
        model.addAttribute("comments", commentRepository.findAll().stream()
                .sorted((a, b) -> b.getCreatedAt().compareTo(a.getCreatedAt()))
                .toList());
        return "index";
    }

    @PostMapping("/comments")
    public String createComment(@RequestParam("author") String author,
                                @RequestParam("content") String content) {
        String normalizedAuthor = author == null ? "" : author.trim();
        String normalizedContent = content == null ? "" : content.trim();

        if (!normalizedAuthor.isBlank() && !normalizedContent.isBlank()) {
            Comment comment = new Comment();
            comment.setAuthor(normalizedAuthor);
            comment.setContent(normalizedContent);
            commentRepository.save(comment);
        }

        return "redirect:/";
    }

    @GetMapping("/search")
    public String search(@RequestParam(name = "q", defaultValue = "") String query, Model model) {
        List<Comment> comments = query.isBlank()
                ? List.of()
                : commentRepository.findByContentContainingIgnoreCaseOrderByCreatedAtDesc(query.trim());

        model.addAttribute("query", query);
        model.addAttribute("comments", comments);
        return "search";
    }
}
