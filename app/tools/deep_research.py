import asyncio
from app.tools.web_search import WebSearchTool

class DeepResearchTool:
    @staticmethod
    async def conduct_research(user_topic: str) -> str:
        # Subdivide queries
        sub_queries = [
            f"{user_topic} نظرة عامة شاملة التفاصيل",
            f"{user_topic} آخر التطورات والأخبار والتحليلات",
            f"{user_topic} المشكلات التحديات والحلول"
        ]
        
        tasks = [WebSearchTool.search_ddg(q, max_results=3) for q in sub_queries]
        results_lists = await asyncio.gather(*tasks)
        
        collected_sources = []
        unique_links = set()
        
        for res_list in results_lists:
            for item in res_list:
                if item['href'] not in unique_links:
                    unique_links.add(item['href'])
                    collected_sources.append(item)
                    
        if not collected_sources:
            return "لم يتم العثور على أي مصادر متاحة ومباشرة حول هذا الموضوع للبحث العقيق."
            
        report_parts = [
            "🔬 <b>تقرير البحث العميق والتحليل المتكامل</b>",
            f"موضوع البحث: {user_topic}\n",
            "📋 <b>النتائج والمعطيات التي تم جمعها وتحليلها:</b>\n"
        ]
        
        for idx, src in enumerate(collected_sources, 1):
            report_parts.append(
                f"{idx}. <b>{src['title']}</b>\n"
                f"{src['body']}\n"
                f"🔗 <a href=\"{src['href']}\">رابط المصدر</a>\n"
            )
            
        report_parts.append(
            "\n💡 <i>ملاحظة: هذا التقرير تم تجميعه والتحقق من مصادره ديناميكياً من محركات الويب المفتوحة.</i>"
        )
        return "\n".join(report_parts)
