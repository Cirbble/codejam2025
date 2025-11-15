import { Component, Input, OnChanges, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CoinPost } from '../../models/coin.model';

@Component({
  selector: 'app-post-display',
  imports: [CommonModule],
  templateUrl: './post-display.html',
  styleUrl: './post-display.css'
})
export class PostDisplayComponent implements OnChanges, OnInit {
  @Input() post?: CoinPost;
  
  visibleCommentsCount = 3;
  readonly initialCommentsCount = 3;
  readonly loadMoreCount = 5;

  ngOnInit() {
    console.log('PostDisplay initialized with post:', this.post);
  }

  ngOnChanges() {
    // Reset visible comments count when post changes
    this.visibleCommentsCount = this.initialCommentsCount;
    
    console.log('=== POST DISPLAY DEBUG ===');
    console.log('Post object:', this.post);
    console.log('Post exists?', !!this.post);
    if (this.post) {
      console.log('Post title:', this.post.title);
      console.log('Comments array:', this.post.comments);
      console.log('Comments is array?', Array.isArray(this.post.comments));
      console.log('Comments length:', this.post.comments?.length);
      if (this.post.comments) {
        console.log('First comment:', this.post.comments[0]);
      }
    }
    console.log('=== END DEBUG ===');
  }

  getVisibleComments(): string[] {
    if (!this.post?.comments) return [];
    return this.post.comments.slice(0, this.visibleCommentsCount);
  }

  hasMoreComments(): boolean {
    if (!this.post?.comments) return false;
    return this.visibleCommentsCount < this.post.comments.length;
  }

  getRemainingCommentsCount(): number {
    if (!this.post?.comments) return 0;
    return this.post.comments.length - this.visibleCommentsCount;
  }

  loadMoreComments(): void {
    this.visibleCommentsCount += this.loadMoreCount;
  }
}
