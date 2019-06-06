//
//  main.m
//  debug_malloc
//
//  Created by Leo on 2019/6/6.
//

#import <Foundation/Foundation.h>
#import <malloc/malloc.h>

int main(int argc, const char * argv[]) {
    @autoreleasepool {
		void *t = calloc(1, 24);
		NSLog(@"%zu", malloc_size(t));
    }
    return 0;
}
