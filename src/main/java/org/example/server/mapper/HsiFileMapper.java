package org.example.server.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.example.server.domain.HsiFile;

@Mapper
public interface HsiFileMapper extends BaseMapper<HsiFile> {
}